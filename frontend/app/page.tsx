export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-16">
      <section className="mx-auto flex max-w-2xl flex-col gap-8 rounded-xl bg-white p-8 shadow-sm">
        <header className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
            Net Zero AI Self-Assessment
          </p>
          <h1 className="text-3xl font-semibold text-slate-900">
            Get a tailored net‑zero roadmap for your site
          </h1>
          <p className="text-base text-slate-600">
            Answer a short questionnaire about your business, energy use, and
            systems. We&apos;ll generate a baseline and a set of prioritised
            recommendations to help you cut carbon and costs.
          </p>
        </header>
        <div className="flex flex-col gap-3 text-sm text-slate-700">
          <p>
            You can save your answers as a draft on this device and return
            later. It usually takes around{" "}
            <span className="font-medium">10–15 minutes</span> to complete.
          </p>
        </div>
        <div>
          <a
            href="/questionnaire"
            className="inline-flex items-center justify-center rounded-md bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
            aria-label="Start the energy questionnaire"
          >
            Start questionnaire
          </a>
        </div>
      </section>
    </main>
  );
}
