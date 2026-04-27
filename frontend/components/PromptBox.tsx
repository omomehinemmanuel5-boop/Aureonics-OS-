'use client';

type PromptBoxProps = {
  prompt: string;
  setPrompt: (value: string) => void;
  onRun: () => void;
  isRunning: boolean;
  buttonText?: string;
};

export function PromptBox({ prompt, setPrompt, onRun, isRunning, buttonText = 'Run Prompt' }: PromptBoxProps) {
  return (
    <div className="rounded-xl2 border border-slate-200 bg-white p-5 shadow-card">
      <label htmlFor="prompt" className="mb-2 block text-sm font-medium text-slate-700">
        Prompt
      </label>
      <textarea
        id="prompt"
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        className="h-28 w-full rounded-xl border border-slate-300 p-3 text-sm outline-none ring-0 transition focus:border-slate-500"
      />
      <button
        onClick={onRun}
        disabled={isRunning || !prompt.trim()}
        className="mt-4 inline-flex rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isRunning ? 'Running…' : buttonText}
      </button>
    </div>
  );
}
