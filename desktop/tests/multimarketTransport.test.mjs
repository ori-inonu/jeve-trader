import test from 'node:test';
import assert from 'node:assert/strict';
import { createSharedEventSubscription } from '../src/multimarketSubscriptions.ts';

test('StrictMode cleanup keeps one shared engine listener active for the remaining subscriber', async () => {
  let registrations = 0;
  let detachments = 0;
  let emit;
  const subscriptions = createSharedEventSubscription((receive) => {
    registrations += 1;
    emit = receive;
    return () => { detachments += 1; };
  });
  const firstValues = [];
  const secondValues = [];

  const setup1 = subscriptions.subscribe(value => firstValues.push(value));
  const setup2 = subscriptions.subscribe(value => secondValues.push(value));
  const [cleanup1, cleanup2] = await Promise.all([setup1, setup2]);
  cleanup1();
  emit({ sequence: 1 });

  assert.equal(registrations, 1);
  assert.deepEqual(firstValues, []);
  assert.deepEqual(secondValues, [{ sequence: 1 }]);
  assert.equal(detachments, 0);

  cleanup1();
  cleanup2();
  emit({ sequence: 2 });
  assert.deepEqual(secondValues, [{ sequence: 1 }]);
  assert.equal(detachments, 1);
});
