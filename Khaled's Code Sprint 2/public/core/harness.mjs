import {DEMO_EXAM_ID, requireUuid} from './ids.mjs';
// Standalone pages only. Embedded callers supply their own exam ID and token provider.
export function configureHarness(config, modeInput, examInput) {
  const liveExamId = config.examId || examInput.value;
  requireUuid(liveExamId, 'examId');
  const apply = () => { examInput.value = modeInput.value === 'demo' ? DEMO_EXAM_ID : liveExamId; };
  modeInput.value = config.mode === 'demo' ? 'demo' : 'live';
  modeInput.addEventListener('change', apply);
  apply();
}
