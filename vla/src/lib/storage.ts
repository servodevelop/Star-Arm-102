let database: Promise<IDBDatabase> | undefined;
function result<T>(request: IDBRequest<T>) {
  return new Promise<T>((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
function open(name: string) {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(name, 1);
    request.onupgradeneeded = () => request.result.createObjectStore("data");
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
async function connect() {
  const current = await open("vla-arms-agent");
  try {
    if (await result(current.transaction("data").objectStore("data").count())) return current;
    // One-time, same-origin migration. Existing new-name data always wins.
    const existing = new Set((await indexedDB.databases()).map((d) => d.name));
    for (const legacyName of ["vlm-arms-agent", "browser-arm"]) {
      if (!existing.has(legacyName)) continue;
      const legacy = await open(legacyName);
      try {
        const store = legacy.transaction("data").objectStore("data");
        const [keys, values] = await Promise.all([result(store.getAllKeys()), result(store.getAll())]);
        if (!keys.length) continue;
        await new Promise<void>((resolve, reject) => {
          const transaction = current.transaction("data", "readwrite");
          const target = transaction.objectStore("data");
          const count = target.count();
          count.onsuccess = () => {
            if (!count.result) keys.forEach((key, i) => target.put(values[i], key));
          };
          transaction.oncomplete = () => resolve();
          transaction.onabort = () => reject(transaction.error);
          transaction.onerror = () => reject(transaction.error);
        });
        return current;
      } finally { legacy.close(); }
    }
    return current;
  } catch (error) {
    current.close();
    throw error;
  }
}
function db() {
  return (database ??= connect().catch((error) => {
    database = undefined;
    throw error;
  }));
}
export async function load<T>(key: string): Promise<T | undefined> {
  const database = await db();
  return result<T | undefined>(database.transaction("data").objectStore("data").get(key));
}
export async function save(key: string, value: unknown) {
  const database = await db();
  return new Promise<void>((resolve, reject) => {
    const transaction = database.transaction("data", "readwrite");
    transaction.objectStore("data").put(value, key);
    transaction.oncomplete = () => resolve();
    transaction.onabort = () => reject(transaction.error);
    transaction.onerror = () => reject(transaction.error);
  });
}
