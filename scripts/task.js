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

let lastTaskId = '';
let taskIdCounter = 0;

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
  const iso = new Date().toISOString();
  let newId = iso.replace(/[-:T.]/g, '').slice(0, 17);
  
  if (newId === lastTaskId) {
    taskIdCounter++;
    newId = newId + String(taskIdCounter).padStart(3, '0');
  } else {
    lastTaskId = newId;
    taskIdCounter = 0;
  }
  return newId;
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

function getTaskById(id, data) {
  if (data.current?.id === id) return data.current;
  for (const t of data.queue) if (t.id === id) return t;
  for (const t of data.completed) if (t.id === id) return t;
  return null;
}

function isTaskReady(task, data) {
  if (!task.depends_on || task.depends_on.length === 0) return true;
  const completedIds = data.completed.map(t => t.id);
  return task.depends_on.every(id => completedIds.includes(id));
}

// ── commands ──────────────────────────────────────────────────────────────────

function cmdStatus() {
  const data = load();
  const task = data.current;
  if (!task) {
    console.log('No task in progress.');
    const nextReady = data.queue.find(t => isTaskReady(t, data));
    if (nextReady) {
      console.log(`\nNext ready: ${nextReady.description}`);
      console.log(`Run: task resume`);
    } else if (data.queue.length) {
      console.log(`\nQueued (${data.queue.length}): all blocked by dependencies`);
      data.queue.forEach(t => {
        if (t.depends_on?.length) {
          const depNames = t.depends_on
            .map(id => getTaskById(id, data)?.description || '?')
            .join(', ');
          console.log(`  [blocked] ${t.description} — waiting on: ${depNames}`);
        }
      });
    } else {
      console.log('Queue is empty.');
    }
    return;
  }
  const done = completedSteps(task);
  const next = nextStep(task);
  const typeLabel = task.plan_type === 'l3-planning' ? ' [planning task]' : task.plan_type === 'l2' ? ' [L2 design task]' : '';
  console.log(`Task:   ${task.description}${typeLabel}`);
  console.log(`Branch: ${task.branch}`);
  console.log(`Plan:   ${task.plan}`);
  console.log(`Done:   ${done.join(', ') || 'none'}`);
  if (next === 'plan_written' && task.plan_type === 'l3-planning') {
    console.log(`Next:   /forge plan  ← write L3 implementation plan for this sub-task`);
  } else if (next) {
    console.log(`Next:   ${next} — ${STEP_DESC[next]}`);
  } else {
    console.log(`Next:   merge, then run: task finish`);
  }
  if (task.subtask_ids?.length) {
    const descs = task.subtask_ids.map(id => {
      const st = getTaskById(id, data);
      return st ? st.description : '?';
    }).join(', ');
    console.log(`Subtasks (${task.subtask_ids.length}): ${descs}`);
  }
  if (data.queue.length) {
    console.log(`\nQueued (${data.queue.length}):`);
    data.queue.forEach(t => {
      const ready = isTaskReady(t, data);
      const status = ready ? '[ready]' : `[blocked]`;
      let prefix = '  • ';
      if (t.parent_id) prefix = '  ↳ ';
      console.log(`${prefix}${status} ${t.description}`);
    });
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
    parent_id: null, subtask_ids: [], depends_on: [], status: 'ready',
  };
  save(data);
  commit(`task: start — ${desc}`);
  console.log(`Started: ${desc}`);
  console.log(`Branch:  ${br}`);
  console.log(`Next:    /forge plan  ← write L3 task plan (writing-plans skill)`);
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

  const unblocked = [];
  for (const qtask of data.queue) {
    if (qtask.status === 'ready') continue;
    if (!qtask.depends_on?.length) {
      qtask.status = 'ready';
      unblocked.push(qtask.description);
    } else if (qtask.depends_on.every(id => data.completed.map(c => c.id).includes(id))) {
      qtask.status = 'ready';
      unblocked.push(qtask.description);
    }
  }

  save(data);
  commit(`task: finish — ${task.description}`);
  console.log(`✓ Finished: ${task.description}`);
  console.log(`  Completed: ${data.completed.length} | Queued: ${data.queue.length}`);
  if (unblocked.length) console.log(`  Unblocked: ${unblocked.join(', ')}`);
  if (data.queue.length) {
    const nextReady = data.queue.find(t => isTaskReady(t, data));
    if (nextReady) console.log(`  Next up:   ${nextReady.description}`);
  }
}

function cmdQueue([...rest]) {
  const desc = rest.join(' ');
  if (!desc) { console.error('Usage: task queue <description>'); process.exit(1); }
  const data = load();
  data.queue.push({
    id: taskId(), description: desc,
    depends_on: [], status: 'ready', parent_id: null, subtask_ids: [],
    steps: Object.fromEntries(STEPS.map(s => [s, false])),
    started: now(), updated: now(),
  });
  save(data);
  commit(`task: queue — ${desc}`);
  console.log(`Queued: ${desc}  (depth: ${data.queue.length})`);
}

function parseSection(lines, headingPattern) {
  let startIdx = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].match(headingPattern)) { startIdx = i; break; }
  }
  if (startIdx === -1) return [];
  const items = [];
  const nameToId = {};
  for (let i = startIdx + 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    if (line.match(/^#{1,2}\s/)) break;
    const match = line.match(/^\d+\.\s+(.+?)(?:\s*\(depends on:\s*(.+?)\))?$/);
    if (!match) continue;
    const desc = match[1].trim();
    const depStr = match[2]?.trim() || '';
    const deps = depStr ? depStr.split(',').map(d => d.trim()) : [];
    const tid = taskId();
    items.push({ desc, deps, tid });
    nameToId[desc] = tid;
  }
  return { items, nameToId };
}

function cmdExtractPlan([planFile]) {
  const data = load();
  if (!data.current) {
    console.error('No task in progress. Start a task first.');
    process.exit(1);
  }

  const file = planFile || data.current.plan;
  const root = repoRoot();
  const fullPath = path.join(root, file);

  if (!fs.existsSync(fullPath)) {
    console.error(`Plan file not found: ${file}`);
    process.exit(1);
  }

  const content = fs.readFileSync(fullPath, 'utf8');
  const lines = content.split('\n');

  // Parse ### Subtasks (implementation tasks) and ### Sub-plans (L2→L3 planning tasks)
  const subtaskResult   = parseSection(lines, /^###\s+Subtasks?/i);
  const subplanResult   = parseSection(lines, /^###\s+Sub-plans?/i);

  const hasSubtasks = subtaskResult.items?.length > 0;
  const hasSubplans = subplanResult.items?.length > 0;

  if (!hasSubtasks && !hasSubplans) {
    console.log('No ### Subtasks or ### Sub-plans section found in plan.');
    return;
  }

  // Merge nameToId maps so cross-section deps resolve
  const nameToId = { ...subtaskResult.nameToId, ...subplanResult.nameToId };

  const createdTasks = [];

  function createQueueEntries(items, planType) {
    for (const st of items) {
      const dependsOn = st.deps
        .map(depName => nameToId[depName])
        .filter(id => id);

      const task = {
        id: st.tid,
        description: st.desc,
        branch: data.current.branch,
        plan: data.current.plan,
        plan_type: planType,
        steps: Object.fromEntries(STEPS.map(s => [s, false])),
        last_completed: null,
        started: now(),
        updated: now(),
        parent_id: data.current.id,
        subtask_ids: [],
        depends_on: dependsOn,
        status: dependsOn.length === 0 ? 'ready' : 'blocked',
      };

      data.queue.push(task);
      createdTasks.push({ desc: st.desc, planType, status: task.status, deps: st.deps });
    }
  }

  if (hasSubtasks) createQueueEntries(subtaskResult.items, 'l3');
  if (hasSubplans) createQueueEntries(subplanResult.items, 'l3-planning');

  const allItems = [
    ...(hasSubtasks ? subtaskResult.items : []),
    ...(hasSubplans ? subplanResult.items : []),
  ];
  if (!data.current.subtask_ids) data.current.subtask_ids = [];
  data.current.subtask_ids.push(...allItems.map(s => s.tid));
  data.current.updated = now();

  save(data);
  commit(`task: extract plan — ${createdTasks.length} tasks`);

  console.log(`Extracted ${createdTasks.length} tasks:`);
  createdTasks.forEach(t => {
    const typeLabel = t.planType === 'l3-planning' ? '[plan]' : '[impl]';
    const status = t.status === 'ready' ? '[ready]' : `[blocked: ${t.deps.join(', ')}]`;
    console.log(`  ${typeLabel} ${status} ${t.desc}`);
  });
}

function cmdResume() {
  const data = load();
  if (data.current) {
    console.log('Task in progress:');
    cmdStatus();
    return;
  }

  let nextIdx = -1;
  for (let i = 0; i < data.queue.length; i++) {
    if (isTaskReady(data.queue[i], data)) {
      nextIdx = i;
      break;
    }
  }

  if (nextIdx === -1) {
    if (data.queue.length) {
      console.log('All queued tasks are blocked by dependencies.');
      console.log('Waiting for:');
      data.queue.forEach(t => {
        if (t.depends_on?.length) {
          const depNames = t.depends_on
            .map(id => getTaskById(id, data)?.description || '?')
            .join(', ');
          console.log(`  ${t.description} — waiting on: ${depNames}`);
        }
      });
    } else {
      console.log('Queue is empty.');
    }
    return;
  }

  const task = data.queue[nextIdx];
  data.current = task;
  data.queue.splice(nextIdx, 1);

  save(data);
  commit(`task: resume — ${task.description}`);

  console.log(`\nResuming: ${task.description}`);
  console.log(`Branch:  ${task.branch}`);
  console.log(`Plan:    ${task.plan}`);
  const next = nextStep(task);
  if (next === 'plan_written' && task.plan_type === 'l3-planning') {
    console.log(`Next:    /forge plan  ← this is a planning task — write the L3 implementation plan`);
  } else if (next) {
    console.log(`Next:    ${next} — ${STEP_DESC[next]}`);
  }
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
  data.queue.forEach(t => {
    const ready = isTaskReady(t, data);
    const status = ready ? '[ready]' : '[blocked]';
    let prefix = '  • ';
    if (t.parent_id) prefix = '  ↳ ';
    console.log(`${prefix}${status} ${t.description}`);
  });
  console.log(`Completed (${data.completed.length}):`);
  data.completed.slice(-5).forEach(t => console.log(`  ✓ ${t.description}`));
}

function cmdSetPlan([planPath]) {
  if (!planPath) { console.error('Usage: task set-plan <plan-file-path>'); process.exit(1); }
  const data = load();
  if (!data.current) { console.error('No task in progress.'); process.exit(1); }
  const root = repoRoot();
  const rel = path.relative(root, path.resolve(planPath));
  data.current.plan = rel;
  data.current.updated = now();
  save(data);
  commit(`task: plan path — ${rel}`);
  console.log(`Plan set: ${rel}`);
}

function cmdCurrentDesc() {
  const data = load();
  if (!data.current) { console.error('No task in progress.'); process.exit(1); }
  process.stdout.write(data.current.description);
}

const COMMANDS = {
  status: cmdStatus, start: cmdStart, done: cmdDone,
  finish: cmdFinish, queue: cmdQueue, resume: cmdResume,
  'extract-plan': cmdExtractPlan, next: cmdNext, list: cmdList,
  'set-plan': cmdSetPlan, 'current-desc': cmdCurrentDesc,
};

const [,, cmd = 'status', ...args] = process.argv;
const fn = COMMANDS[cmd];
if (!fn) {
  console.error(`Unknown command: ${cmd}\nAvailable: ${Object.keys(COMMANDS).join(', ')}`);
  process.exit(1);
}
fn(args);
