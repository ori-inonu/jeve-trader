export type EventDetach = () => void;
export type EventAttach<T> = (publish: (value: T) => void) => EventDetach | Promise<EventDetach>;

export interface SharedEventSubscription<T> {
  publish(value: T): void;
  subscribe(callback: (value: T) => void): Promise<EventDetach>;
}

export function createSharedEventSubscription<T>(attach: EventAttach<T>): SharedEventSubscription<T> {
  const listeners = new Map<symbol, (value: T) => void>();
  let attachPromise: Promise<void> | null = null;
  let detachTransport: EventDetach | null = null;

  const publish = (value: T) => {
    for (const listener of [...listeners.values()]) listener(value);
  };

  const subscribe = async (callback: (value: T) => void): Promise<EventDetach> => {
    const id = Symbol();
    listeners.set(id, callback);

    if (!detachTransport && !attachPromise) {
      attachPromise = Promise.resolve()
        .then(() => attach(publish))
        .then(detach => { detachTransport = detach; })
        .catch(error => {
          attachPromise = null;
          throw error;
        });
    }

    try {
      if (attachPromise) await attachPromise;
    } catch (error) {
      listeners.delete(id);
      throw error;
    }

    let cleaned = false;
    return () => {
      if (cleaned) return;
      cleaned = true;
      listeners.delete(id);
      if (listeners.size === 0 && detachTransport) {
        const detach = detachTransport;
        detachTransport = null;
        attachPromise = null;
        detach();
      }
    };
  };

  return { publish, subscribe };
}
