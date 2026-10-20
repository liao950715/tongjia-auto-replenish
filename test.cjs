const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function harness(data = new Map(), failSave = false) {
  const elements = new Map();
  const el = selector => {
    if (!elements.has(selector)) elements.set(selector, {
      innerHTML: "", textContent: "", value: "", style: {}, disabled: false,
      classList: { toggle() {}, contains() { return false; } },
      setAttribute() {}, addEventListener() {}, onclick: null
    });
    return elements.get(selector);
  };
  const storage = {
    getItem: key => data.get(key) ?? null,
    setItem: (key, value) => { if (failSave) throw Error("storage full"); data.set(key, value); }
  };
  const context = vm.createContext({
    Intl, Date, console, setTimeout: () => 0, clearTimeout() {},
    localStorage: storage, document: { querySelector: el, querySelectorAll: () => [] },
    window: { scrollTo() {} }
  });
  vm.runInContext(fs.readFileSync(__dirname + "/app.js", "utf8"), context);
  return { run: code => vm.runInContext(code, context), data, el };
}

const t = harness();
const run = t.run;
assert.equal(run("stats().total"), 72);
assert.equal(run("stats().suggested"), 72);
assert.equal(run("stats().count"), 6);
assert.equal(run("stats().low"), 2);
assert.equal(run("JSON.stringify(PRODUCTS.map(p=>calc(p).suggested))"), "[35,16,10,5,3,3,0,0]");
assert.equal(run("validQty(-1)||validQty(1.5)||validQty(Infinity)||validQty(1000000)"), false);
assert.equal(run('updateQty("P006","")'), false);
assert.equal(run('updateQty("P006","1000")'), true);
assert.equal(run("canSubmit()"), false);
assert.equal(run("stats().total"), 1069);
run('state.draft.P006.reason="活動團購";state.draft.P006.confirmed=true');
assert.equal(run("canSubmit()"), true);
run('updateQty("P006","1001")');
assert.equal(run("canSubmit()"), false);
run("state.draft.P006.confirmed=true;submit()");
assert.equal(run("state.orders.length"), 1);
assert.equal(run('state.orders[0].items.find(r=>r.id==="P006").qty'), 1001);
assert.equal(run("state.orders[0].status"), "已送至統家");
assert.equal(run("state.orders[0].storeId"), "S001");
assert.match(t.el("#main").innerHTML, /已送至統家（模擬）/);
run("submit()");
assert.equal(run("state.orders.length"), 1);
assert.equal(run('updateQty("P006","4")'), false);

run('selectStore("S002")');
assert.equal(run("activeStore().id"), "S002");
assert.equal(t.el("#store-switch").value, "S002");
assert.match(t.el("#breadcrumb").textContent, /站前門市/);
assert.notEqual(run("stats().suggested"), 72);
assert.equal(run("state.orders.length"), 0);
assert.equal(run('updateQty("P001","99")'), true);
assert.equal(run("state.draft.P001.qty"), 99);
run('selectStore("S003")');
assert.equal(run("state.draft.P001.qty"), run('calc(PRODUCTS[0]).suggested'));
assert.equal(run("state.orders.length"), 0);
run('selectStore("S002")');
assert.equal(run("state.draft.P001.qty"), 99);
run('selectStore("S001")');
assert.equal(run("state.orders.length"), 1);
const id = run("state.orders[0].id");
run('navigate("confirm")');
assert.equal(run(`receiveOrder(${JSON.stringify(id)})`), true);
assert.equal(run("state.orders[0].status"), "總部已接收");
assert.ok(run("state.orders[0].receivedAt"));
assert.match(t.el("#main").innerHTML, /總部已接收（模擬）/);
assert.equal(run(`receiveOrder(${JSON.stringify(id)})`), false);
assert.equal(run("state.orders.length"), 1);

const restored = harness(t.data);
assert.equal(restored.run("activeStore().id"), "S001");
assert.equal(restored.run("state.orders[0].status"), "總部已接收");
restored.run('selectStore("S002")');
assert.equal(restored.run("state.draft.P001.qty"), 99);
assert.equal(restored.run("state.orders.length"), 0);

const legacy = new Map([["tongjia-workbench-v2", JSON.stringify({
  date: restored.run("dateAt()"),
  draft: JSON.parse(t.data.get("tongjia-workbench-v3")).stores.S001.draft,
  orders: [{ id: "TJ-OLD", items: [], status: "本機示範，未傳送總部" }],
  submitted: "TJ-OLD"
})]]);
const migrated = harness(legacy);
assert.equal(migrated.run("state.orders[0].status"), "舊版示範訂單");
assert.equal(migrated.run("state.submitted"), "TJ-OLD");

const failed = harness(new Map(), true);
failed.run("submit()");
assert.equal(failed.run("state.orders.length"), 0);
assert.equal(failed.run("state.submitted"), null);
assert.equal(run("isSpecial(23,3)"), true);
assert.equal(run("isSpecial(22,3)"), false);
assert.equal(run("isSpecial(20,0)"), true);
assert.equal(run('esc("<img onerror=x>")'), "&lt;img onerror=x&gt;");
console.log("PASS: model, input validation, special confirmation, per-store isolation and persistence, simulated delivery lifecycle, duplicate prevention, storage failure.");
