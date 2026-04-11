#!/usr/bin/env node
// Purpose: CLI task queue manager — persists workflow progress across sessions and LLM handoffs.

const fs   = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');

const STEPS = [
  'plan_written', 'plan_approved', 'implemented',
  'regression', 'compliance', 'developer', 'qa',
  'specialist', 'user_review', 'merged'
];

const STEP_DESC = {
  plan_written:  'L3 task plan written (writing-plans skill)',
  plan_approved: 'Plan approved by compliance agent',
  implemented:   'Implementer subagent done (TDD — all tests pass)',
  regression:    'Regression agent passed (blast radius + affected test suites)',
  compliance:    'Compliance agent passed (diff matches plan)',
  developer:     'Developer agent passed (code quality + SOLID)',
  qa:            'QA agent passed (test coverage + correctness)',
  specialist:    'Role-specific agent passed (architect/ml/a2a/api-security)',
  user_review:   'User reviewed and approved',
  merged:        'Squash merged to main, branch deleted',
};

function repoRoot() {
  return execSync('git rev-parse --show-toplevel', { encoding: 'utf8' }).trim();
}

function queuePath() {
  return path.join(repoRoot(), 'tasks', 'queue.json');
}

function load() {
  const p = queuePath();
  if (!fs.existsSync(p)) return { current: null, queue: [], completed: [] };
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function save(data) {
  const p = queuePath();
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(data, null, 2));
}

function commit(msg) {
  const root = repoRoot();
  spawnSync('git', ['add', queuePath()], { cwd: root, stdio: 'inherit' });
  spawnSync('git', ['commit', '-m', msg], { cwd: root, stdio: 'inherit' });
}

function branch() {
  return execSync('git branch --show-current', { encoding: 'utf8' }).trim();
}

function now() {
  return new Date().toISOString();
}

function taskId() {
  return new Date().toISOString().replace(/[-:T]/g, '').slice(0, 12);
}

function findPlan(br) {
  const root = repoRoot();
  const svc  = br.replace(/^task\//, '').split('/')[0];
  const dirs = [
    path.join(root, 'services', svc, 'docs', 'plans'),
    path.join(root, 'docs', 'plans'),
  ];
  for (const d of dirs) {
    if (!fs.existsSync(d)) continue;
    const files = fs.readdirSync(d).filter(f => f.endsWith('.md')).sort().reverse();
    if (files.length) return path.relative(root, path.join(d, files[0]));
  }
  return 'docs/plans/<add-plan-path>';
}

function nextStep(task) {
  return STEPS.find(s => !task.steps[s]) || null;
}

function completedSteps(task) {
  return STEPS.filter(s => task.steps[s]);
}

// ── commands ──────────────────────────────────────────────────────────────────

function cmdStatus() {
  const data = load();
  const task = data.current;
  if (!task) {
    console.log('No task in progress.');
    if (data.queue.length) {
      console.log(`\nQueued (${data.queue.length}):`);
      data.queue.forEach(t => console.log(`  • ${t.description}`));
    }
    return;
  }
  const done = completedSteps(task);
  const next = nextStep(task);
  console.log(`Task:   ${task.description}`);
  console.log(`Branch: ${task.branch}`);
  console.log(`Plan:   ${task.plan}`);
  console.log(`Done:   ${done.join(', ') || 'none'}`);
  if (next) console.log(`Next:   ${next} — ${STEP_DESC[next]}`);
  else      console.log(`Next:   merge, then run: task finish`);
  if (data.queue.length) {
    console.log(`\nQueued (${data.queue.length}):`);
    data.queue.forEach(t => console.log(`  • ${t.description}`));
  }
}

function cmdStart([...rest]) {
  const desc = rest.join(' ');
  if (!desc) { console.error('Usage: task start <description>'); process.exit(1); }
  const data = load();
  if (data.current) {
    console.error(`Task already in progress: ${data.current.description}`);
    console.error('Run: task finish  — to complete it first.');
    process.exit(1);
  }
  const br = branch();
  data.current = {
    id: taskId(), description: desc, branch: br, plan: findPlan(br),
    steps: Object.fromEntries(STEPS.map(s => [s, false])),
    last_completed: null, started: now(), updated: now(),
  };
  save(data);
  commit(`task: start — ${desc}`);
  console.log(`Started: ${desc}`);
  console.log(`Branch:  ${br}`);
  console.log(`Next:    plan_written — ${STEP_DESC.plan_written}`);
}

function cmdDone([step]) {
  if (!step || !STEPS.includes(step)) {
    console.error(`Usage: task done <step>\nSteps: ${STEPS.join(', ')}`);
    process.exit(1);
  }
  const data = load();
  if (!data.current) { console.error('No task in progress.'); process.exit(1); }
  data.current.steps[step] = true;
  data.current.last_completed = step;
  data.current.updated = now();
  save(data);
  commit(`task: step done — ${step}`);
  const next = nextStep(data.current);
  console.log(`✓ ${step}`);
  if (next) console.log(`→ Next: ${next} — ${STEP_DESC[next]}`);
  else      console.log('All steps done. Merge, then run: task finish');
}

function cmdFinish() {
  const data = load();
  if (!data.current) { console.error('No task in progress.'); process.exit(1); }
  const task = data.current;
  task.steps.merged = true;
  task.last_completed = 'merged';
  task.updated = now();
  data.completed.push(task);
  data.current = null;
  save(data);
  commit(`task: finish — ${task.description}`);
  console.log(`✓ Finished: ${task.description}`);
  console.log(`  Completed: ${data.completed.length} | Queued: ${data.queue.length}`);
  if (data.queue.length) console.log(`  Next up:   ${data.queue[0].description}`);
}

function cmdQueue([...rest]) {
  const desc = rest.join(' ');
  if (!desc) { console.error('Usage: task queue <description>'); process.exit(1); }
  const data = load();
  data.queue.push({ id: taskId(), description: desc, status: 'queued' });
  save(data);
  commit(`task: queue — ${desc}`);
  console.log(`Queued: ${desc}  (depth: ${data.queue.length})`);
}

function cmdNext() {
  const data = load();
  if (!data.current) { console.error('No task in progress.'); process.exit(1); }
  const task = data.current;
  const next = nextStep(task);
  const done = completedSteps(task);
  console.log('='.repeat(60));
  console.log('TASK HANDOFF — resume from here');
  console.log('='.repeat(60));
  console.log(`Task:      ${task.description}`);
  console.log(`Branch:    ${task.branch}`);
  console.log(`Plan:      ${task.plan}`);
  console.log(`Last done: ${task.last_completed || 'nothing yet'}`);
  if (next) {
    console.log(`Next step: ${next}`);
    console.log(`What:      ${STEP_DESC[next]}`);
  }
  console.log('\nInstructions:');
  console.log(`  1. git checkout ${task.branch}`);
  console.log(`  2. Read the plan: ${task.plan}`);
  console.log(`  3. Complete step: ${next}`);
  console.log(`  4. Run: task done ${next}`);
  console.log(`  5. Run: task next  (for the step after)`);
  if (done.length) console.log(`\nDo NOT redo: ${done.join(', ')}`);
  console.log('='.repeat(60));
}

function cmdList() {
  const data = load();
  const task = data.current;
  console.log(`Current:   ${task ? task.description : 'none'}`);
  if (task) {
    const done = completedSteps(task);
    const next = nextStep(task);
    console.log(`  Done:  ${done.join(', ') || 'none'}`);
    console.log(`  Next:  ${next || 'merge'}`);
  }
  console.log(`Queued (${data.queue.length}):`);
  data.queue.forEach(t => console.log(`  • [${t.id}] ${t.description}`));
  console.log(`Completed (${data.completed.length}):`);
  data.completed.slice(-5).forEach(t => console.log(`  ✓ ${t.description}`));
}

const COMMANDS = {
  status: cmdStatus, start: cmdStart, done: cmdDone,
  finish: cmdFinish, queue: cmdQueue, next: cmdNext, list: cmdList,
};

const [,, cmd = 'status', ...args] = process.argv;
const fn = COMMANDS[cmd];
if (!fn) {
  console.error(`Unknown command: ${cmd}\nAvailable: ${Object.keys(COMMANDS).join(', ')}`);
  process.exit(1);
}
fn(args);
