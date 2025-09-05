#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for LinkedIn-like Job Portal
Tests all core backend functionality including authentication, jobs, applications, and dashboard.
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("❌ Could not get backend URL from frontend/.env")
    sys.exit(1)

print(f"🔗 Testing backend at: {BASE_URL}")

# Test data
test_users = {
    'job_seeker': {
        'email': 'sarah.johnson@email.com',
        'password': 'securepass123',
        'name': 'Sarah Johnson',
        'user_type': 'job_seeker'
    },
    'employer': {
        'email': 'hr.manager@techcorp.com', 
        'password': 'hrpass456',
        'name': 'HR Manager',
        'user_type': 'employer'
    }
}

test_job = {
    'title': 'Senior Software Engineer',
    'company': 'TechCorp Solutions',
    'location': 'San Francisco, CA',
    'job_type': 'full-time',
    'salary_range': '$120,000 - $160,000',
    'description': 'We are looking for an experienced software engineer to join our growing team. You will work on cutting-edge projects using modern technologies.',
    'requirements': ['5+ years Python experience', 'Experience with FastAPI/Django', 'Strong problem-solving skills'],
    'benefits': ['Health insurance', 'Remote work options', '401k matching', 'Professional development budget']
}

# Global variables to store test data
registered_users = {}
created_jobs = {}
created_applications = {}

def make_request(method, endpoint, data=None, params=None):
    """Helper function to make HTTP requests"""
    url = f"{BASE_URL}/api{endpoint}"
    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=params, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, params=params, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, params=params, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_user_registration():
    """Test user registration for both job seekers and employers"""
    print("\n🧪 Testing User Registration...")
    
    success_count = 0
    total_tests = len(test_users)
    
    for user_type, user_data in test_users.items():
        print(f"  📝 Registering {user_type}: {user_data['email']}")
        
        response = make_request('POST', '/auth/register', user_data)
        if not response:
            print(f"    ❌ Failed to make request")
            continue
            
        if response.status_code == 200:
            try:
                user_response = response.json()
                registered_users[user_type] = user_response
                print(f"    ✅ Registration successful - ID: {user_response['id']}")
                
                # Verify response structure
                required_fields = ['id', 'email', 'name', 'user_type', 'created_at']
                missing_fields = [field for field in required_fields if field not in user_response]
                if missing_fields:
                    print(f"    ⚠️  Missing fields in response: {missing_fields}")
                else:
                    success_count += 1
                    
            except json.JSONDecodeError:
                print(f"    ❌ Invalid JSON response")
        else:
            print(f"    ❌ Registration failed - Status: {response.status_code}, Response: {response.text}")
    
    # Test duplicate registration
    print(f"  🔄 Testing duplicate registration...")
    duplicate_response = make_request('POST', '/auth/register', test_users['job_seeker'])
    if duplicate_response and duplicate_response.status_code == 400:
        print(f"    ✅ Duplicate registration properly rejected")
        success_count += 0.5
    else:
        print(f"    ❌ Duplicate registration not handled properly")
    
    print(f"📊 Registration Tests: {success_count}/{total_tests + 0.5} passed")
    return success_count >= total_tests

def test_user_login():
    """Test user login functionality"""
    print("\n🧪 Testing User Login...")
    
    success_count = 0
    total_tests = len(test_users) + 1  # +1 for invalid login test
    
    for user_type, user_data in test_users.items():
        print(f"  🔐 Logging in {user_type}: {user_data['email']}")
        
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        
        response = make_request('POST', '/auth/login', login_data)
        if not response:
            print(f"    ❌ Failed to make request")
            continue
            
        if response.status_code == 200:
            try:
                user_response = response.json()
                print(f"    ✅ Login successful - User: {user_response['name']}")
                
                # Verify response matches registration
                if user_type in registered_users:
                    reg_user = registered_users[user_type]
                    if user_response['id'] == reg_user['id'] and user_response['email'] == reg_user['email']:
                        success_count += 1
                    else:
                        print(f"    ❌ Login response doesn't match registration data")
                else:
                    success_count += 1
                    
            except json.JSONDecodeError:
                print(f"    ❌ Invalid JSON response")
        else:
            print(f"    ❌ Login failed - Status: {response.status_code}, Response: {response.text}")
    
    # Test invalid login
    print(f"  🚫 Testing invalid login...")
    invalid_login = {'email': 'nonexistent@email.com', 'password': 'wrongpass'}
    invalid_response = make_request('POST', '/auth/login', invalid_login)
    if invalid_response and invalid_response.status_code == 401:
        print(f"    ✅ Invalid login properly rejected")
        success_count += 1
    else:
        print(f"    ❌ Invalid login not handled properly")
    
    print(f"📊 Login Tests: {success_count}/{total_tests} passed")
    return success_count >= total_tests - 1

def test_job_management():
    """Test job posting, fetching, and search functionality"""
    print("\n🧪 Testing Job Management...")
    
    if 'employer' not in registered_users:
        print("❌ No employer user available for job testing")
        return False
    
    employer = registered_users['employer']
    success_count = 0
    total_tests = 6
    
    # Test job posting
    print(f"  📝 Creating job post...")
    job_params = {'employer_id': employer['id']}
    response = make_request('POST', '/jobs', test_job, params=job_params)
    
    if response and response.status_code == 200:
        try:
            job_response = response.json()
            created_jobs['main_job'] = job_response
            print(f"    ✅ Job created successfully - ID: {job_response['id']}")
            
            # Verify job data
            if (job_response['title'] == test_job['title'] and 
                job_response['employer_id'] == employer['id']):
                success_count += 1
            else:
                print(f"    ❌ Job data mismatch")
                
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Job creation failed - Status: {response.status_code if response else 'No response'}")
    
    # Test fetching all jobs
    print(f"  📋 Fetching all jobs...")
    response = make_request('GET', '/jobs')
    if response and response.status_code == 200:
        try:
            jobs = response.json()
            if isinstance(jobs, list) and len(jobs) > 0:
                print(f"    ✅ Retrieved {len(jobs)} jobs")
                success_count += 1
            else:
                print(f"    ❌ No jobs returned or invalid format")
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Failed to fetch jobs")
    
    # Test job search
    print(f"  🔍 Testing job search...")
    search_params = {'search': 'Software Engineer'}
    response = make_request('GET', '/jobs', params=search_params)
    if response and response.status_code == 200:
        try:
            jobs = response.json()
            if isinstance(jobs, list):
                print(f"    ✅ Search returned {len(jobs)} jobs")
                success_count += 1
            else:
                print(f"    ❌ Invalid search response format")
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Job search failed")
    
    # Test location filter
    print(f"  📍 Testing location filter...")
    location_params = {'location': 'San Francisco'}
    response = make_request('GET', '/jobs', params=location_params)
    if response and response.status_code == 200:
        try:
            jobs = response.json()
            if isinstance(jobs, list):
                print(f"    ✅ Location filter returned {len(jobs)} jobs")
                success_count += 1
            else:
                print(f"    ❌ Invalid location filter response")
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Location filter failed")
    
    # Test job type filter
    print(f"  💼 Testing job type filter...")
    type_params = {'job_type': 'full-time'}
    response = make_request('GET', '/jobs', params=type_params)
    if response and response.status_code == 200:
        try:
            jobs = response.json()
            if isinstance(jobs, list):
                print(f"    ✅ Job type filter returned {len(jobs)} jobs")
                success_count += 1
            else:
                print(f"    ❌ Invalid job type filter response")
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Job type filter failed")
    
    # Test fetching specific job
    if 'main_job' in created_jobs:
        print(f"  🎯 Fetching specific job...")
        job_id = created_jobs['main_job']['id']
        response = make_request('GET', f'/jobs/{job_id}')
        if response and response.status_code == 200:
            try:
                job = response.json()
                if job['id'] == job_id:
                    print(f"    ✅ Retrieved specific job successfully")
                    success_count += 1
                else:
                    print(f"    ❌ Job ID mismatch")
            except json.JSONDecodeError:
                print(f"    ❌ Invalid JSON response")
        else:
            print(f"    ❌ Failed to fetch specific job")
    
    print(f"📊 Job Management Tests: {success_count}/{total_tests} passed")
    return success_count >= total_tests - 1

def test_job_applications():
    """Test job application system"""
    print("\n🧪 Testing Job Application System...")
    
    if 'job_seeker' not in registered_users or 'main_job' not in created_jobs:
        print("❌ Missing job seeker or job for application testing")
        return False
    
    job_seeker = registered_users['job_seeker']
    job = created_jobs['main_job']
    success_count = 0
    total_tests = 5
    
    # Test job application
    print(f"  📤 Applying for job...")
    application_data = {
        'job_id': job['id'],
        'cover_letter': 'I am very interested in this position and believe my skills in Python and FastAPI make me a great fit for your team.'
    }
    app_params = {'applicant_id': job_seeker['id']}
    
    response = make_request('POST', '/applications', application_data, params=app_params)
    if response and response.status_code == 200:
        try:
            app_response = response.json()
            created_applications['main_app'] = app_response
            print(f"    ✅ Application submitted successfully - ID: {app_response['id']}")
            
            # Verify application data
            if (app_response['job_id'] == job['id'] and 
                app_response['applicant_id'] == job_seeker['id']):
                success_count += 1
            else:
                print(f"    ❌ Application data mismatch")
                
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Application submission failed - Status: {response.status_code if response else 'No response'}")
    
    # Test duplicate application prevention
    print(f"  🚫 Testing duplicate application prevention...")
    duplicate_response = make_request('POST', '/applications', application_data, params=app_params)
    if duplicate_response and duplicate_response.status_code == 400:
        print(f"    ✅ Duplicate application properly rejected")
        success_count += 1
    else:
        print(f"    ❌ Duplicate application not handled properly")
    
    # Test fetching user applications
    print(f"  📋 Fetching user applications...")
    response = make_request('GET', f'/applications/user/{job_seeker["id"]}')
    if response and response.status_code == 200:
        try:
            applications = response.json()
            if isinstance(applications, list) and len(applications) > 0:
                print(f"    ✅ Retrieved {len(applications)} user applications")
                # Check if job details are enriched
                app = applications[0]
                if 'job_title' in app and 'company' in app:
                    print(f"    ✅ Application enriched with job details")
                    success_count += 1
                else:
                    print(f"    ⚠️  Application not enriched with job details")
                    success_count += 0.5
            else:
                print(f"    ❌ No applications returned")
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Failed to fetch user applications")
    
    # Test fetching job applications
    print(f"  📊 Fetching job applications...")
    response = make_request('GET', f'/applications/job/{job["id"]}')
    if response and response.status_code == 200:
        try:
            applications = response.json()
            if isinstance(applications, list) and len(applications) > 0:
                print(f"    ✅ Retrieved {len(applications)} job applications")
                # Check if applicant details are enriched
                app = applications[0]
                if 'applicant_name' in app:
                    print(f"    ✅ Application enriched with applicant details")
                    success_count += 1
                else:
                    print(f"    ⚠️  Application not enriched with applicant details")
                    success_count += 0.5
            else:
                print(f"    ❌ No applications returned")
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Failed to fetch job applications")
    
    # Test application status tracking
    if 'main_app' in created_applications:
        print(f"  📈 Verifying application status...")
        app = created_applications['main_app']
        if app.get('status') == 'pending':
            print(f"    ✅ Application status correctly set to 'pending'")
            success_count += 1
        else:
            print(f"    ❌ Application status incorrect: {app.get('status')}")
    
    print(f"📊 Application Tests: {success_count}/{total_tests} passed")
    return success_count >= total_tests - 1

def test_dashboard_statistics():
    """Test dashboard statistics for both user types"""
    print("\n🧪 Testing Dashboard Statistics...")
    
    success_count = 0
    total_tests = 2
    
    # Test job seeker dashboard
    if 'job_seeker' in registered_users:
        print(f"  📊 Testing job seeker dashboard...")
        job_seeker = registered_users['job_seeker']
        params = {'user_id': job_seeker['id'], 'user_type': 'job_seeker'}
        
        response = make_request('GET', '/dashboard/stats', params=params)
        if response and response.status_code == 200:
            try:
                stats = response.json()
                required_fields = ['total_applications', 'pending', 'shortlisted']
                if all(field in stats for field in required_fields):
                    print(f"    ✅ Job seeker stats: {stats}")
                    success_count += 1
                else:
                    print(f"    ❌ Missing required fields in job seeker stats")
            except json.JSONDecodeError:
                print(f"    ❌ Invalid JSON response")
        else:
            print(f"    ❌ Failed to fetch job seeker stats")
    
    # Test employer dashboard
    if 'employer' in registered_users:
        print(f"  📈 Testing employer dashboard...")
        employer = registered_users['employer']
        params = {'user_id': employer['id'], 'user_type': 'employer'}
        
        response = make_request('GET', '/dashboard/stats', params=params)
        if response and response.status_code == 200:
            try:
                stats = response.json()
                required_fields = ['total_jobs', 'active_jobs', 'total_applications']
                if all(field in stats for field in required_fields):
                    print(f"    ✅ Employer stats: {stats}")
                    success_count += 1
                else:
                    print(f"    ❌ Missing required fields in employer stats")
            except json.JSONDecodeError:
                print(f"    ❌ Invalid JSON response")
        else:
            print(f"    ❌ Failed to fetch employer stats")
    
    print(f"📊 Dashboard Tests: {success_count}/{total_tests} passed")
    return success_count >= total_tests - 1

def test_user_profile_management():
    """Test user profile fetch and update"""
    print("\n🧪 Testing User Profile Management...")
    
    if 'job_seeker' not in registered_users:
        print("❌ No job seeker available for profile testing")
        return False
    
    job_seeker = registered_users['job_seeker']
    success_count = 0
    total_tests = 2
    
    # Test fetching user profile
    print(f"  👤 Fetching user profile...")
    response = make_request('GET', f'/users/{job_seeker["id"]}')
    if response and response.status_code == 200:
        try:
            user_profile = response.json()
            if user_profile['id'] == job_seeker['id']:
                print(f"    ✅ Profile fetched successfully")
                success_count += 1
            else:
                print(f"    ❌ Profile ID mismatch")
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Failed to fetch user profile")
    
    # Test updating user profile
    print(f"  ✏️  Updating user profile...")
    profile_update = {
        'title': 'Senior Python Developer',
        'bio': 'Experienced software developer with expertise in Python, FastAPI, and web development.',
        'location': 'New York, NY',
        'skills': ['Python', 'FastAPI', 'React', 'MongoDB']
    }
    
    response = make_request('PUT', f'/users/{job_seeker["id"]}/profile', profile_update)
    if response and response.status_code == 200:
        try:
            result = response.json()
            if 'message' in result and 'success' in result['message'].lower():
                print(f"    ✅ Profile updated successfully")
                success_count += 1
            else:
                print(f"    ❌ Unexpected update response: {result}")
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
    else:
        print(f"    ❌ Failed to update profile")
    
    print(f"📊 Profile Tests: {success_count}/{total_tests} passed")
    return success_count >= total_tests - 1

def run_all_tests():
    """Run all backend tests and provide summary"""
    print("🚀 Starting Comprehensive Backend API Testing")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests in order
    test_results['registration'] = test_user_registration()
    test_results['login'] = test_user_login()
    test_results['job_management'] = test_job_management()
    test_results['applications'] = test_job_applications()
    test_results['dashboard'] = test_dashboard_statistics()
    test_results['profile'] = test_user_profile_management()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Backend APIs are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the detailed output above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)