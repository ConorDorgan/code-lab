/* Web Worker — loads Pyodide from CDN and runs Python code */
let pyodide = null;

async function initPyodide() {
  importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js');
  pyodide = await loadPyodide();
}

const ready = initPyodide();

self.onmessage = async (e) => {
  const { id, code } = e.data;
  await ready;

  const output = [];

  pyodide.setStdout({ batched: (s) => output.push(s) });
  pyodide.setStderr({ batched: (s) => output.push(`[31m${s}[0m`) });

  try {
    await pyodide.runPythonAsync(code);
    self.postMessage({ id, ok: true, output: output.join('\n') });
  } catch (err) {
    self.postMessage({ id, ok: false, output: output.join('\n'), error: err.message });
  }
};
