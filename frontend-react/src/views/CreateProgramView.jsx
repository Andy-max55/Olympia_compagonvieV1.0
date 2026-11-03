import { useState } from "react";

const TITLE_FONT = { fontFamily: '"Cormorant Garamond", Georgia, serif' };
const BODY_FONT = { fontFamily: "Inter, system-ui, sans-serif" };

function CreateProgramView() {
  const [programName, setProgramName] = useState("");
  const [detailedObjective, setDetailedObjective] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    console.log({ programName, detailedObjective });
  }

  return (
    <main
      className="min-h-dvh w-full max-w-full overflow-x-hidden bg-[#0a0a0a] px-4 py-8 text-white sm:px-6 md:py-16"
      style={BODY_FONT}
    >
      <div className="mx-auto flex w-full min-w-0 max-w-xl flex-col">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-red-500">Olympia</p>
        <h1 className="mt-3 text-4xl font-light italic leading-tight text-white sm:text-5xl" style={TITLE_FONT}>
          Nouveau programme
        </h1>
        <p className="mt-3 max-w-full text-sm leading-relaxed text-gray-400 sm:text-base">
          Pose le cadre. Le détail viendra ensuite.
        </p>

        <form className="mt-8 flex w-full min-w-0 flex-col gap-6" onSubmit={handleSubmit}>
          <div className="flex min-w-0 flex-col gap-2">
            <label htmlFor="program-name" className="text-sm text-gray-300">
              Nom du programme
            </label>
            <input
              id="program-name"
              name="programName"
              type="text"
              value={programName}
              onChange={(event) => setProgramName(event.target.value)}
              placeholder="Force, 8 semaines"
              autoComplete="off"
              className="min-h-12 w-full min-w-0 rounded-2xl border border-white/10 bg-white/[0.04] px-4 text-base text-white outline-none placeholder:text-gray-500 focus:border-white/25"
            />
          </div>

          <div className="flex min-w-0 flex-col gap-2">
            <label htmlFor="detailed-objective" className="text-sm text-gray-300">
              Objectif détaillé
            </label>
            <div className="min-w-0 rounded-3xl border border-white/10 bg-white/[0.03] p-3 sm:p-4">
              <textarea
                id="detailed-objective"
                name="detailedObjective"
                value={detailedObjective}
                onChange={(event) => setDetailedObjective(event.target.value)}
                placeholder="Décris ce que ce programme doit changer."
                rows={8}
                className="min-h-40 w-full min-w-0 resize-y bg-transparent text-base leading-relaxed text-white outline-none placeholder:text-gray-500"
              />
              {/* TODO: Insérer le composant AudioRecorder ici */}
              <div className="mt-3 min-h-14 w-full rounded-2xl border border-dashed border-white/15" aria-hidden="true" />
            </div>
          </div>

          <button
            type="submit"
            className="min-h-12 w-full rounded-full bg-red-600 px-6 text-sm font-medium text-white transition-colors hover:bg-red-500 sm:w-auto"
          >
            Créer mon programme
          </button>
        </form>
      </div>
    </main>
  );
}

export default CreateProgramView;
