import { Check } from 'lucide-react'

const features = [
  'AI-powered skill extraction from your resume',
  'Smart job matching with gap analysis',
  'Actionable suggestions to land more interviews',
]

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      {/* Brand panel — hidden on mobile */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-gradient-to-br from-indigo-950 via-indigo-900 to-indigo-800 p-12 text-white">
        <div className="flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-white/15 text-sm font-bold">
            R
          </div>
          <span className="text-sm font-semibold tracking-tight">ResumeAI</span>
        </div>

        <div className="space-y-8">
          <div className="space-y-3">
            <h1 className="text-4xl font-bold leading-tight tracking-tight">
              Land your next<br />dream role.
            </h1>
            <p className="text-indigo-200 text-lg leading-relaxed">
              AI-powered resume analysis and job matching that tells you exactly what's missing.
            </p>
          </div>

          <ul className="space-y-3">
            {features.map((f) => (
              <li key={f} className="flex items-start gap-3 text-sm text-indigo-100">
                <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-white/15">
                  <Check size={11} strokeWidth={2.5} />
                </span>
                {f}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-indigo-400">© {new Date().getFullYear()} ResumeAI</p>
      </div>

      {/* Form panel */}
      <div className="flex flex-1 items-center justify-center bg-background px-6 py-12">
        {children}
      </div>
    </div>
  )
}
