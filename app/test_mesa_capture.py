import unittest
from unittest.mock import patch
import profit_bridge as bridge
from app_core import ObservationSession


class MesaCaptureTests(unittest.TestCase):
    def test_rejected_book_never_replaces_the_accepted_observation(self):
        from dataclasses import replace
        from copy import deepcopy
        ts=1791293400000
        health=bridge.SourceHealth('fixture',True,False,ts,ts)
        book=dict(symbol='WINV26',bids=[dict(price_points=129995,quantity=15)],asks=[dict(price_points=130005,quantity=25)],market_ts_ms=ts,captured_at_ms=ts)
        batch=bridge.SourceBatch([],[],health,[],books=[book])
        session=ObservationSession('WINV26')
        with patch('app_core.time.time',return_value=ts/1000):
            session.ingest(batch)
            rejected=deepcopy(book); rejected['market_ts_ms']-=1; rejected['bids'][0]['quantity']=999
            state=session.ingest(replace(batch,books=[rejected]))
        self.assertEqual(state['order_flow']['book']['bids'][0]['quantity'],15)
        self.assertEqual(len(state['order_flow']['book_history']),1)
        self.assertIn('Snapshot do livro rejeitado: OUT_OF_ORDER_OR_CONFLICTING_BOOK',state['warnings'])

    def test_exported_book_depth_matches_the_calculation_limit(self):
        from flow_engine import FlowEngine
        ts=1791293400000
        rows=[['bid','bidqty','ask','askqty','ts_ms']]+[[129995-i*5,15,130005+i*5,25,ts] for i in range(256)]
        books=bridge.parse_book_rows(rows,'WINV26',ts)
        engine=FlowEngine('WINV26')
        self.assertTrue(engine.set_book({**books,'ts_ms':ts})['accepted'])
        self.assertEqual(engine.snapshot(ts)['evidence_coverage']['depth_levels']['bids'],256)

    def test_sample_change_and_polling_intervals_reach_source_evidence(self):
        ts=1791293400000
        quote=[['symbol','last','ts_ms'],['WINV26',130000,ts]]
        changed=[['symbol','last','ts_ms'],['WINV26',130005,ts+500]]
        with patch.object(bridge,'_load_comtypes',return_value=object()), patch.object(bridge.os,'name','nt'), \
             patch.object(bridge,'_read_excel_com_ranges',side_effect=[[quote],[quote],[changed]]), \
             patch('profit_bridge.time.time',side_effect=[ts/1000,ts/1000,ts/1000,(ts+250)/1000,(ts+250)/1000,(ts+250)/1000,(ts+500)/1000,(ts+500)/1000,(ts+500)/1000]):
            reader=bridge.CombinedExcelBridge('Mesa.xlsx','Cotacoes','A1:C2','','',symbol='WINV26')
            reader.read()
            unchanged=reader.read()
            updated=reader.read()
        self.assertEqual(unchanged.evidence['polling_effective_ms'],250)
        self.assertIsNone(unchanged.evidence['rtd_change_interval_ms'])
        self.assertEqual(updated.evidence['rtd_change_interval_ms'],500)

    def test_coincident_trades_brokers_book_and_vap_are_separate_observations(self):
        ts = 1791293400000
        quote = [['symbol','last','ts_ms'], ['WINV26',130000,ts]]
        tape = [['id','symbol','ts_ms','price','quantity','aggressor','corretora compradora','corretora vendedora'],
                ['1','WINV26',ts,130000,2,'buy','A','B'], ['2','WINV26',ts,130000,2,'buy','A','B']]
        book = [['bid','bidqty','ask','askqty','ts_ms'], [129995,15,130005,25,ts]]
        vap = [['price','quantity'],[130000,1000]]
        with patch.object(bridge, '_load_comtypes', return_value=object()), patch.object(bridge, '_read_excel_com_ranges', return_value=[quote,tape,book,vap]), patch.object(bridge.os,'name','nt'), patch('profit_bridge.time.time', return_value=ts/1000):
            reader = bridge.CombinedExcelBridge('Mesa.xlsx','Cotacoes','A1:C2','Negocios','A1:H3',symbol='WINV26',
                book_sheet='Livro',book_range='A1:E2',vap_sheet='VAP',vap_range='A1:B2')
            batch = reader.read()
            repeated = reader.read()
        self.assertEqual(len(batch.events),2)
        self.assertEqual(len(repeated.events),0)
        self.assertEqual(batch.events[0].buyer_broker,'A')
        self.assertFalse(batch.health.complete)
        with patch('app_core.time.time', return_value=ts/1000):
            state = ObservationSession('WINV26').ingest(batch)
        self.assertEqual(state['computed_features']['total_contracts'],4)
        self.assertEqual(state['order_flow']['brokers'][0]['net_contracts'],4)
        self.assertFalse(state['order_flow']['investor_positions_known'])
        self.assertEqual(state['order_flow']['book']['bids'][0]['quantity'],15)
        self.assertEqual(state['order_flow']['volume_at_price'][0]['quantity'],1000)
        self.assertTrue(batch.capabilities['buyer_broker'])

    def test_rtd_throttle_is_opt_in_and_restores_only_the_value_it_changed(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        excel=SimpleNamespace(RTD=SimpleNamespace(ThrottleInterval=2000))
        native=SimpleNamespace(CoInitialize=Mock(),CoUninitialize=Mock())
        client=SimpleNamespace(GetActiveObject=Mock(return_value=excel))
        guard=bridge.RtdThrottleGuard(com_modules=(native,client))
        self.assertEqual(excel.RTD.ThrottleInterval,2000)
        self.assertEqual(guard.enable()['previous_ms'],2000)
        self.assertEqual(excel.RTD.ThrottleInterval,250)
        self.assertTrue(guard.restore()['restored'])
        self.assertEqual(excel.RTD.ThrottleInterval,2000)
        guard.enable()
        excel.RTD.ThrottleInterval=500 # an external change must survive
        self.assertFalse(guard.restore()['restored'])
        self.assertEqual(excel.RTD.ThrottleInterval,500)


if __name__=='__main__': unittest.main()
