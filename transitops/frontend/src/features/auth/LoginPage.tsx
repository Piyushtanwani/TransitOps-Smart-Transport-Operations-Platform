import React, { useState } from 'react';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { Checkbox } from '../../components/ui/Checkbox';

const roleOptions = [
  { label: 'Fleet Manager', value: 'fleet_manager' },
  { label: 'Dispatcher', value: 'dispatcher' },
  { label: 'Safety Officer', value: 'safety_officer' },
  { label: 'Financial Analyst', value: 'financial_analyst' },
];

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('dispatcher');

  const handleRoleSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = e.target.value;
    setRole(selected);
    if (selected === 'dispatcher') {
      setEmail('dispatcher@transitops.in');
      setPassword('password123');
    } else if (selected === 'fleet_manager') {
      setEmail('fleet@transitops.in');
      setPassword('password123');
    } else if (selected === 'safety_officer') {
      setEmail('safety@transitops.in');
      setPassword('password123');
    } else if (selected === 'financial_analyst') {
      setEmail('finance@transitops.in');
      setPassword('password123');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Login attempt', { email, password });
  };

  return (
    <div className="flex min-h-screen bg-surface-0 font-sans">
      {/* Left Panel */}
      <div className="hidden w-2/5 flex-col justify-between bg-[#C8CFD7] p-12 lg:flex text-black">
        <div>
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded bg-[#D4A373]/30">
            {/* Placeholder logo matching the hatched box in mockup */}
            <div className="h-10 w-10 border border-[#D4A373]" style={{ backgroundImage: 'repeating-linear-gradient(45deg, #D4A373 25%, transparent 25%, transparent 75%, #D4A373 75%, #D4A373), repeating-linear-gradient(45deg, #D4A373 25%, #C8CFD7 25%, #C8CFD7 75%, #D4A373 75%, #D4A373)', backgroundPosition: '0 0, 4px 4px', backgroundSize: '8px 8px' }} />
          </div>
          <h1 className="font-heading text-4xl font-bold tracking-tight text-gray-900">TransitOps</h1>
          <p className="mt-2 text-lg text-gray-700">Smart Transport Operations Platform</p>
        </div>
        
        <div>
          <p className="mb-4 font-medium text-gray-900">One login, four roles:</p>
          <ul className="space-y-3 text-gray-800">
            <li className="flex items-center"><span className="mr-3 h-2 w-2 rounded-full bg-signal"></span> Fleet Manager</li>
            <li className="flex items-center"><span className="mr-3 h-2 w-2 rounded-full bg-signal"></span> Dispatcher</li>
            <li className="flex items-center"><span className="mr-3 h-2 w-2 rounded-full bg-signal"></span> Safety Officer</li>
            <li className="flex items-center"><span className="mr-3 h-2 w-2 rounded-full bg-signal"></span> Financial Analyst</li>
          </ul>
        </div>
        
        <div className="text-sm font-medium tracking-widest text-gray-500 uppercase">
          TRANSITOPS © 2026 · PUBLIC BETA
        </div>
      </div>

      {/* Right Panel */}
      <div className="flex w-full flex-col items-center justify-center p-8 lg:w-3/5">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <h2 className="text-3xl font-semibold text-on-surface font-heading">Sign in to your account</h2>
            <p className="mt-2 text-sm text-on-surface-variant">Enter your credentials to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input 
              label="Email" 
              type="email" 
              placeholder="e.g. dispatcher@transitops.in" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
            />
            
            <Input 
              label="Password" 
              type="password" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
            
            <Select 
              label="Role (Quick)" 
              options={roleOptions} 
              value={role}
              onChange={handleRoleSelect}
            />

            <div className="flex items-center justify-between pt-2">
              <Checkbox label="Remember me" />
              <a href="#" className="text-sm font-medium text-signal hover:underline">
                Forgot password?
              </a>
            </div>

            <Button type="submit" className="w-full mt-2" size="lg">
              Sign In
            </Button>
          </form>

          <div className="mt-10 text-sm text-on-surface-variant">
            <p className="mb-3">Access is scoped by role after login:</p>
            <ul className="space-y-2">
              <li>+ Fleet Manager → Fleet, Maintenance</li>
              <li>+ Dispatcher → Dashboard, Trips</li>
              <li>+ Safety Officer → Drivers, Compliance</li>
              <li>+ Financial Analyst → Fuel & Expenses, Analytics</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
