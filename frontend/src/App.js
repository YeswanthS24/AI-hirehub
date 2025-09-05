import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const userData = response.data;
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      return userData;
    } catch (error) {
      throw error;
    }
  };

  const register = async (email, password, name, userType) => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email,
        password,
        name,
        user_type: userType
      });
      const userData = response.data;
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      return userData;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);

// Components
const Header = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('jobs');

  return (
    <header className="header-gradient shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-4">
            <div className="logo-container">
              <h1 className="text-2xl font-bold text-white">HireHub</h1>
            </div>
            {user && (
              <nav className="hidden md:flex space-x-8 ml-8">
                <button
                  onClick={() => setActiveTab('jobs')}
                  className={`nav-link ${activeTab === 'jobs' ? 'active' : ''}`}
                >
                  Jobs
                </button>
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
                >
                  Dashboard
                </button>
                {user.user_type === 'employer' && (
                  <button
                    onClick={() => setActiveTab('post-job')}
                    className={`nav-link ${activeTab === 'post-job' ? 'active' : ''}`}
                  >
                    Post Job
                  </button>
                )}
              </nav>
            )}
          </div>
          
          {user && (
            <div className="flex items-center space-x-4">
              <div className="profile-container">
                <div className="profile-avatar">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <span className="text-white font-medium">{user.name}</span>
              </div>
              <button
                onClick={logout}
                className="btn-secondary"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

const LoginForm = () => {
  const { login } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    userType: 'job_seeker'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        const { register } = useAuth();
        await register(formData.email, formData.password, formData.name, formData.userType);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
      <div className="auth-card">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {isLogin ? 'Welcome Back' : 'Join HireHub'}
          </h2>
          <p className="text-gray-600">
            {isLogin ? 'Sign in to your account' : 'Create your account'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {!isLogin && (
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                type="text"
                className="form-input"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              className="form-input"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label className="form-label">I am a</label>
              <select
                className="form-input"
                value={formData.userType}
                onChange={(e) => setFormData({...formData, userType: e.target.value})}
              >
                <option value="job_seeker">Job Seeker</option>
                <option value="employer">Employer</option>
              </select>
            </div>
          )}

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
          </button>
        </div>
      </div>
    </div>
  );
};

const JobCard = ({ job, onApply, showApplyButton = true }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="job-card">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">{job.title}</h3>
          <p className="text-lg text-blue-600 font-medium">{job.company}</p>
          <div className="flex items-center space-x-4 mt-2 text-gray-600">
            <span className="flex items-center">
              📍 {job.location}
            </span>
            <span className="job-type-badge">
              {job.job_type}
            </span>
            {job.salary_range && (
              <span className="text-green-600 font-medium">
                💰 {job.salary_range}
              </span>
            )}
          </div>
        </div>
      </div>

      <p className="text-gray-700 mb-4">
        {isExpanded ? job.description : `${job.description.substring(0, 150)}...`}
      </p>

      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-blue-600 hover:text-blue-800 mb-4 font-medium"
      >
        {isExpanded ? 'Show Less' : 'Read More'}
      </button>

      {isExpanded && (
        <div className="space-y-3 mb-4 animate-fadeIn">
          {job.requirements.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Requirements:</h4>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {job.requirements.map((req, idx) => (
                  <li key={idx}>{req}</li>
                ))}
              </ul>
            </div>
          )}
          {job.benefits.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Benefits:</h4>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {job.benefits.map((benefit, idx) => (
                  <li key={idx}>{benefit}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-500">
          Posted: {new Date(job.posted_at).toLocaleDateString()}
        </span>
        {showApplyButton && (
          <button
            onClick={() => onApply(job.id)}
            className="btn-primary"
          >
            Apply Now
          </button>
        )}
      </div>
    </div>
  );
};

const JobsPage = () => {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    search: '',
    location: '',
    job_type: ''
  });

  const fetchJobs = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.location) params.append('location', filters.location);
      if (filters.job_type) params.append('job_type', filters.job_type);

      const response = await axios.get(`${API}/jobs?${params}`);
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [filters]);

  const handleApply = async (jobId) => {
    try {
      await axios.post(`${API}/applications?applicant_id=${user.id}`, {
        job_id: jobId
      });
      alert('Application submitted successfully!');
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to apply');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Finding amazing opportunities...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Find Your Dream Job</h1>
          
          <div className="filters-container">
            <input
              type="text"
              placeholder="Search jobs, companies..."
              className="form-input flex-1"
              value={filters.search}
              onChange={(e) => setFilters({...filters, search: e.target.value})}
            />
            <input
              type="text"
              placeholder="Location"
              className="form-input w-48"
              value={filters.location}
              onChange={(e) => setFilters({...filters, location: e.target.value})}
            />
            <select
              className="form-input w-48"
              value={filters.job_type}
              onChange={(e) => setFilters({...filters, job_type: e.target.value})}
            >
              <option value="">All Types</option>
              <option value="full-time">Full Time</option>
              <option value="part-time">Part Time</option>
              <option value="contract">Contract</option>
              <option value="remote">Remote</option>
            </select>
          </div>
        </div>

        <div className="jobs-grid">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onApply={handleApply}
              showApplyButton={user?.user_type === 'job_seeker'}
            />
          ))}
        </div>

        {jobs.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No jobs found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({});
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, appsRes] = await Promise.all([
          axios.get(`${API}/dashboard/stats?user_id=${user.id}&user_type=${user.user_type}`),
          user.user_type === 'job_seeker' 
            ? axios.get(`${API}/applications/user/${user.id}`)
            : axios.get(`${API}/jobs/employer/${user.id}`)
        ]);

        setStats(statsRes.data);
        if (user.user_type === 'job_seeker') {
          setApplications(appsRes.data);
        } else {
          setJobs(appsRes.data);
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [user]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Welcome back, {user.name}!
        </h1>

        <div className="stats-grid mb-8">
          {user.user_type === 'job_seeker' ? (
            <>
              <div className="stat-card">
                <div className="stat-number">{stats.total_applications || 0}</div>
                <div className="stat-label">Total Applications</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.pending || 0}</div>
                <div className="stat-label">Pending</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.shortlisted || 0}</div>
                <div className="stat-label">Shortlisted</div>
              </div>
            </>
          ) : (
            <>
              <div className="stat-card">
                <div className="stat-number">{stats.total_jobs || 0}</div>
                <div className="stat-label">Total Jobs Posted</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.active_jobs || 0}</div>
                <div className="stat-label">Active Jobs</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.total_applications || 0}</div>
                <div className="stat-label">Total Applications</div>
              </div>
            </>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">
            {user.user_type === 'job_seeker' ? 'Your Applications' : 'Your Job Posts'}
          </h2>
          
          {user.user_type === 'job_seeker' ? (
            <div className="space-y-4">
              {applications.map((app) => (
                <div key={app.id} className="application-card">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-lg">{app.job_title}</h3>
                      <p className="text-blue-600">{app.company}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        Applied: {new Date(app.applied_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={`status-badge status-${app.status}`}>
                      {app.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="jobs-grid">
              {jobs.map((job) => (
                <JobCard key={job.id} job={job} showApplyButton={false} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const PostJobForm = () => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    location: '',
    job_type: 'full-time',
    salary_range: '',
    description: '',
    requirements: [''],
    benefits: ['']
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const jobData = {
        ...formData,
        requirements: formData.requirements.filter(req => req.trim()),
        benefits: formData.benefits.filter(benefit => benefit.trim())
      };

      await axios.post(`${API}/jobs?employer_id=${user.id}`, jobData);
      alert('Job posted successfully!');
      setFormData({
        title: '',
        company: '',
        location: '',
        job_type: 'full-time',
        salary_range: '',
        description: '',
        requirements: [''],
        benefits: ['']
      });
    } catch (error) {
      alert('Failed to post job');
    } finally {
      setLoading(false);
    }
  };

  const addField = (field) => {
    setFormData({
      ...formData,
      [field]: [...formData[field], '']
    });
  };

  const updateField = (field, index, value) => {
    const updated = [...formData[field]];
    updated[index] = value;
    setFormData({
      ...formData,
      [field]: updated
    });
  };

  const removeField = (field, index) => {
    const updated = formData[field].filter((_, i) => i !== index);
    setFormData({
      ...formData,
      [field]: updated
    });
  };

  return (
    <div className="page-container">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Post a New Job</h1>

        <form onSubmit={handleSubmit} className="job-form">
          <div className="form-group">
            <label className="form-label">Job Title</label>
            <input
              type="text"
              className="form-input"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="form-group">
              <label className="form-label">Company</label>
              <input
                type="text"
                className="form-input"
                value={formData.company}
                onChange={(e) => setFormData({...formData, company: e.target.value})}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Location</label>
              <input
                type="text"
                className="form-input"
                value={formData.location}
                onChange={(e) => setFormData({...formData, location: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="form-group">
              <label className="form-label">Job Type</label>
              <select
                className="form-input"
                value={formData.job_type}
                onChange={(e) => setFormData({...formData, job_type: e.target.value})}
              >
                <option value="full-time">Full Time</option>
                <option value="part-time">Part Time</option>
                <option value="contract">Contract</option>
                <option value="remote">Remote</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Salary Range (Optional)</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., $50,000 - $70,000"
                value={formData.salary_range}
                onChange={(e) => setFormData({...formData, salary_range: e.target.value})}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Job Description</label>
            <textarea
              className="form-input h-32"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Requirements</label>
            {formData.requirements.map((req, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  className="form-input flex-1"
                  value={req}
                  onChange={(e) => updateField('requirements', index, e.target.value)}
                  placeholder="Enter requirement"
                />
                {formData.requirements.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeField('requirements', index)}
                    className="btn-secondary"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => addField('requirements')}
              className="btn-secondary mt-2"
            >
              Add Requirement
            </button>
          </div>

          <div className="form-group">
            <label className="form-label">Benefits</label>
            {formData.benefits.map((benefit, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  className="form-input flex-1"
                  value={benefit}
                  onChange={(e) => updateField('benefits', index, e.target.value)}
                  placeholder="Enter benefit"
                />
                {formData.benefits.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeField('benefits', index)}
                    className="btn-secondary"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => addField('benefits')}
              className="btn-secondary mt-2"
            >
              Add Benefit
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Posting Job...' : 'Post Job'}
          </button>
        </form>
      </div>
    </div>
  );
};

const MainApp = () => {
  const { user, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState('jobs');

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm />;
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'jobs':
        return <JobsPage />;
      case 'dashboard':
        return <Dashboard />;
      case 'post-job':
        return user.user_type === 'employer' ? <PostJobForm /> : <JobsPage />;
      default:
        return <JobsPage />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage={currentPage} setCurrentPage={setCurrentPage} />
      {renderPage()}
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

export default App;