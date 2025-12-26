import React from 'react';

interface LoginPageProps {
  onLogin: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin();
  };

  return (
    <div className="min-h-screen bg-primary text-light-text flex items-center justify-center p-4">
      <div className="absolute inset-0 z-0 opacity-10">
        <div className="absolute -top-1/4 -left-1/4 w-96 h-96 lg:w-[40rem] lg:h-[40rem] bg-accent-blue rounded-full filter blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-1/4 -right-1/4 w-96 h-96 lg:w-[40rem] lg:h-[40rem] bg-accent-blue-light rounded-full filter blur-3xl animate-pulse animation-delay-4000"></div>
      </div>
      
      <main className="relative z-10 container mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div className="text-center md:text-left animate-fade-in">
              <h1 className="text-5xl lg:text-6xl font-bold tracking-tight text-light-text mb-4">
                  The Future of <span className="title-gradient">Collaborative</span> Learning & Building
              </h1>
              <p className="text-lg lg:text-xl text-muted-text max-w-xl mx-auto md:mx-0">
                  EduNex is an all-in-one platform for students to exchange notes, manage projects, and build together in real-time.
              </p>
          </div>

          <div className="w-full max-w-md mx-auto animate-fade-in" style={{animationDelay: '0.2s'}}>
            <div className="glassmorphism rounded-2xl p-8 shadow-2xl shadow-black/20">
              <div className="text-center mb-6">
                <h1 className="text-4xl font-semibold tracking-wide uppercase title-gradient mb-4">
                    EduNex
                </h1>
                <h2 className="text-2xl font-semibold text-light-text">Welcome Back</h2>
                <p className="text-muted-text mt-1">Sign in to continue to your dashboard.</p>
              </div>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-300">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    defaultValue="student@eduspace.io"
                    className="mt-1 block w-full bg-primary/50 border border-gray-700 rounded-lg px-4 py-2 text-light-text focus:outline-none focus:ring-2 focus:ring-accent-blue transition-all"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-300">Password</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    defaultValue="password"
                    className="mt-1 block w-full bg-primary/50 border border-gray-700 rounded-lg px-4 py-2 text-light-text focus:outline-none focus:ring-2 focus:ring-accent-blue transition-all"
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-accent-blue to-accent-blue-light text-white font-semibold py-2.5 px-4 rounded-lg flex items-center justify-center space-x-2 transition-all duration-300 transform hover:scale-105 hover:shadow-glow-blue"
                >
                  <span>Login to Your Workspace</span>
                </button>
              </form>
            </div>
          </div>
      </main>
    </div>
  );
};

export default LoginPage;