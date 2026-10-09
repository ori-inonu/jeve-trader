import test from 'node:test';
import assert from 'node:assert/strict';
import {observableBook,probabilityLabel} from '../src/multimarketView.ts';

const makeState=()=>({origin:'live',book:{valid:true,bids:[['99','1']],asks:[['101','2']]},
  health:[{channel:'depth',valid:true,stale:false,last_receive_time_ms:10000}]});
test('old or invalid book is hidden rather than presented as current depth',()=>{
  const value=makeState();
  assert.equal(observableBook(value,11000),value.book);
  assert.equal(observableBook(value,12001),null);
  assert.equal(observableBook(value,9999),null);
  value.health[0].valid=false;
  assert.equal(observableBook(value,11000),null);
  value.origin='synthetic';
  assert.equal(observableBook(value,11000),null);
  value.health[0].valid=true;value.health[0].stale=true;
  assert.equal(observableBook(value,11000),null);
});
test('unknown target probability remains unknown',()=>{
  assert.equal(probabilityLabel(null),'Não estimada');
  assert.equal(probabilityLabel(undefined),'Não estimada');
});
