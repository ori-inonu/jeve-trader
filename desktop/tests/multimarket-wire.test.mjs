import test from 'node:test';
import assert from 'node:assert/strict';
import {parseMultimarketWire, projectMultimarketEvent} from '../src/multimarketWire.ts';
import {createMultimarketProjector} from '../src/multimarketModel.ts';

test('multimarket accepts outer wire versions 1/2 while retaining inner 3', () => {
  const value={schema_version:3};
  for(const schema_version of [1,2]) assert.equal(parseMultimarketWire({schema_version,result:value}),value);
});
test('unsupported outer/inner event schemas reach the cockpit as a diagnostic', () => {
  for(const wire of [{schema_version:3,result:{schema_version:3}},{schema_version:2,result:{schema_version:2}},{schema_version:2,result:null}]) {
    assert.throws(()=>parseMultimarketWire(wire));
    const view=createMultimarketProjector().project(projectMultimarketEvent(wire),0);
    assert.ok(view.diagnostic);
    assert.equal(view.selected,null);
  }
});
