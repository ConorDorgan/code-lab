/* Web Worker — loads sql.js from public/ and runs SQL against a seeded database */
importScripts('/sql-wasm.js');

let SQL = null;
let seedBytes = null;

const ready = (async () => {
  SQL = await initSqlJs({ locateFile: () => '/sql-wasm.wasm' });

  const res = await fetch('/sql-seed.sql');
  const seedSql = await res.text();

  const seedDb = new SQL.Database();
  seedDb.run(seedSql);
  seedBytes = seedDb.export();
  seedDb.close();
})();

self.onmessage = async (e) => {
  const { id, code, setup } = e.data;
  await ready;

  const db = new SQL.Database(seedBytes);
  try {
    if (setup) db.run(setup);
    const results = db.exec(code);
    db.close();
    self.postMessage({ id, ok: true, results });
  } catch (err) {
    db.close();
    self.postMessage({ id, ok: false, results: [], error: err.message });
  }
};
