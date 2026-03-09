import { useState } from "react";

const Login = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    // Login logic will be added when backend auth is ready
    console.log("Login attempt:", { username, password });
  };

  return (
    <div className="dark min-h-screen flex flex-col relative overflow-hidden bg-background-dark">
      {/* Background Overlay */}
      <div
        className="absolute inset-0 z-0 opacity-10 pointer-events-none bg-center bg-no-repeat bg-cover"
        data-alt="Dark global world map with glowing nodes"
        data-location="Global"
        style={{ backgroundImage: "url('https://placeholder.pics/svg/300')" }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-background-dark/80 via-background-dark/95 to-background-dark" />

      <div className="relative z-10 flex flex-1 flex-col items-center justify-center px-4 py-12">
        {/* Logo & Branding */}
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="bg-primary p-3 rounded-lg shadow-lg shadow-primary/20 mb-4">
            <span className="material-symbols-outlined text-white text-5xl">
              emergency
            </span>
          </div>
          <h1 className="font-oswald text-4xl font-bold tracking-widest text-slate-100 uppercase">
            Okoa Route <span className="text-primary">Command Center</span>
          </h1>
          <div className="mt-2 h-1 w-24 bg-primary rounded-full" />
          <p className="mt-4 text-slate-400 font-medium tracking-tight uppercase text-sm border border-slate-border px-4 py-1 rounded">
            Authorized Personnel Only
          </p>
        </div>

        {/* Login Card */}
        <div className="w-full max-w-md bg-slate-card p-8 rounded-xl border border-slate-border shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Field */}
            <div className="flex flex-col gap-2">
              <label
                className="text-slate-300 text-sm font-semibold uppercase tracking-wider"
                htmlFor="username"
              >
                Username or Email
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">
                  person
                </span>
                <input
                  className="w-full pl-10 pr-4 py-3 bg-slate-input border border-slate-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent text-slate-100 placeholder-slate-500 transition-all outline-none"
                  id="username"
                  name="username"
                  placeholder="Enter credentials"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <label
                  className="text-slate-300 text-sm font-semibold uppercase tracking-wider"
                  htmlFor="password"
                >
                  Password
                </label>
              </div>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">
                  lock
                </span>
                <input
                  className="w-full pl-10 pr-12 py-3 bg-slate-input border border-slate-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent text-slate-100 placeholder-slate-500 transition-all outline-none"
                  id="password"
                  name="password"
                  placeholder="••••••••"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="material-symbols-outlined">
                    {showPassword ? "visibility_off" : "visibility"}
                  </span>
                </button>
              </div>
            </div>

            {/* Login Button */}
            <button
              className="w-full bg-primary hover:bg-red-700 text-white font-oswald font-bold py-4 px-6 rounded-lg uppercase tracking-widest transition-all shadow-lg shadow-primary/30 active:scale-95 flex items-center justify-center gap-2"
              type="submit"
            >
              Login to Command
              <span className="material-symbols-outlined">login</span>
            </button>
          </form>

          {/* Links */}
          <div className="mt-8 pt-6 border-t border-slate-border flex flex-col gap-3 items-center text-sm font-medium">
            <a
              className="text-slate-400 hover:text-primary transition-colors"
              href="#"
            >
              Forgot Password?
            </a>
            <div className="flex items-center gap-2">
              <span className="text-slate-500">Need access?</span>
              <a
                className="text-slate-400 hover:text-primary transition-colors underline underline-offset-4"
                href="#"
              >
                Request Access
              </a>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="mt-12 flex items-center gap-3 px-6 py-2 bg-slate-card/50 border border-slate-border rounded-full">
          <div className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
          </div>
          <span className="text-slate-400 text-xs font-bold uppercase tracking-widest">
            System Secure - Operational
          </span>
          <div className="h-3 w-px bg-slate-border" />
          <span className="text-slate-500 text-[10px] font-mono">
            v4.2.1-HQ
          </span>
        </div>
      </div>

      {/* Footer Security Notice */}
      <footer className="relative z-10 w-full p-6 text-center">
        <p className="text-slate-600 text-[10px] uppercase tracking-[0.2em]">
          Warning: This is a restricted system. Unauthorized access is strictly
          prohibited and monitored.
        </p>
      </footer>
    </div>
  );
};

export default Login;
