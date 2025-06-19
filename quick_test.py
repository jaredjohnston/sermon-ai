from tests.test_complete_flow import TestCompleteFlow

print('🔹 Testing validation service basic logic...')
test = TestCompleteFlow()
test.test_validation_service_basic_logic()
print('✅ Validation service test passed!')

print('🔹 Testing signup data validation...')
test_data = {
    'email': 'test@test.com', 
    'password': 'Test123!', 
    'first_name': 'Test', 
    'last_name': 'User', 
    'country': 'US', 
    'organization_name': 'Test Org'
}
test.test_signup_data_validation(test_data)
print('✅ Signup data validation test passed!')
print('🎉 All core validation tests completed successfully!')