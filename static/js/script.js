
document.getElementById('signup-form').addEventListener('submit', function (event) {
  // Prevent form submission
  event.preventDefault();

  // Get the password and confirm password values
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirm-password').value;

  // Get the warning div to display message
  const warningDiv = document.getElementById('password-warning');

  // Check if the passwords match
  if (password !== confirmPassword) {
      // If passwords don't match, display a warning message
      warningDiv.textContent = "Passwords do not match!";
      warningDiv.style.color = 'red';
  } else {
      // If passwords match, you can submit the form or perform other actions
      warningDiv.textContent = "";
      
      // Submit the form using its ID
      document.getElementById('signup-form').submit();

      //NOTE: IF FOMR DATA IS NOT SUBMITING THEN COMMETNOUT THE UPPER LINE AND UNCOMMENT THE BELOW CODE : "this.submit()"
      // You can uncomment the following line to actually submit the form if desired
      //this.submit();
  }
});

document.getElementById('role-toggle').addEventListener('change', function () {
  var roleInput = document.getElementById('role');
  roleInput.value = this.checked ? 'seller' : 'buyer';
});


document.getElementById('email').addEventListener('blur', function() {
const email = this.value;
const role = document.querySelector('input[name="role"]:checked').value;

fetch('/check-email', {
  method: 'POST',
  body: JSON.stringify({email: email, role: role})
})
  .then(response => response.json())
  .then(data => {
    if (data.exists) {
      // Show error message
      document.getElementById('email-error').textContent = 'Email already exists';
    } else {
      // Clear error message
      document.getElementById('email-error').textContent = '';
    }
  });
});fetch('/check-email', {
method: 'POST',
body: JSON.stringify({email: email, role: role})
})

// max function
function max(arr) {
  let maxVal = arr[0];
  for (let i = 1; i < arr.length; i++) {
    if (arr[i] > maxVal) {
      maxVal = arr[i];
    }
  }
  return maxVal;
}


function openEnquiryModal(element) {
  const propertyType = element.dataset.type;
  const sellerEmail = element.dataset.email;
  // Now use propertyType and sellerEmail as needed in the modal
  console.log(propertyType, sellerEmail);
}


document.addEventListener('DOMContentLoaded', function() {
  // Select the form and submit button
  const propertyForm = document.querySelector('.form-container form');
  const submitButton = propertyForm.querySelector('button[type="submit"]');

  // Function to create and display error message
  function showError(element, message) {
      // Remove any existing error messages
      const existingError = element.parentNode.querySelector('.error-message');
      if (existingError) {
          existingError.remove();
      }

      // Create error message element
      const errorElement = document.createElement('div');
      errorElement.className = 'error-message';
      errorElement.style.color = 'red';
      errorElement.style.fontSize = '0.8em';
      errorElement.style.marginTop = '5px';
      errorElement.textContent = message;

      // Insert error message after the input
      element.parentNode.insertBefore(errorElement, element.nextSibling);
      
      // Highlight the input
      element.style.border = '2px solid red';
  }

  // Function to remove error styling
  function clearError(element) {
      const errorElement = element.parentNode.querySelector('.error-message');
      if (errorElement) {
          errorElement.remove();
      }
      element.style.border = '';
  }

  // Validation function
  function validateForm() {
      let isValid = true;

      // Validate property type
      const propertyTypeSelect = propertyForm.querySelector('select[name="property_type"]');
      if (!propertyTypeSelect.value) {
          showError(propertyTypeSelect, 'Please select a property type');
          isValid = false;
      } else {
          clearError(propertyTypeSelect);
      }

      // Validate city
      const citySelect = propertyForm.querySelector('select[name="city"]');
      if (!citySelect.value) {
          showError(citySelect, 'Please select a city');
          isValid = false;
      } else {
          clearError(citySelect);
      }

      // Validate price
      const priceInput = propertyForm.querySelector('input[name="price"]');
      if (!priceInput.value || isNaN(priceInput.value) || parseFloat(priceInput.value) <= 0) {
          showError(priceInput, 'Please enter a valid price');
          isValid = false;
      } else {
          clearError(priceInput);
      }

      // Validate rent
      const rentInput = propertyForm.querySelector('input[name="rent"]');
      if (!rentInput.value || isNaN(rentInput.value) || parseFloat(rentInput.value) <= 0) {
          showError(rentInput, 'Please enter a valid rent amount');
          isValid = false;
      } else {
          clearError(rentInput);
      }

      // Validate address
      const addressInput = propertyForm.querySelector('input[name="address"]');
      if (!addressInput.value.trim()) {
          showError(addressInput, 'Please enter a property address');
          isValid = false;
      } else {
          clearError(addressInput);
      }

      // Validate file upload
      const fileInput = propertyForm.querySelector('input[type="file"]');
      if (!fileInput.files.length) {
          showError(fileInput, 'Please upload a property photo');
          isValid = false;
      } else {
          // Additional file validation (optional)
          const file = fileInput.files[0];
          const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg'];
          const maxSize = 5 * 1024 * 1024; // 5MB

          if (!allowedTypes.includes(file.type)) {
              showError(fileInput, 'Invalid file type. Please upload JPEG or PNG');
              isValid = false;
          } else if (file.size > maxSize) {
              showError(fileInput, 'File is too large. Maximum size is 5MB');
              isValid = false;
          } else {
              clearError(fileInput);
          }
      }

      return isValid;
  }

  // Add event listeners to inputs for real-time validation
  const inputs = propertyForm.querySelectorAll('input, select');
  inputs.forEach(input => {
      input.addEventListener('input', function() {
          if (this.value.trim() !== '') {
              clearError(this);
          }
      });
  });

  // Form submission handler
  submitButton.addEventListener('click', function(event) {
      event.preventDefault();

      // Validate form
      if (validateForm()) {
          // Create FormData object
          const formData = new FormData(propertyForm);

          // AJAX call to create Razorpay order
          fetch('/create_property_listing_order', {
              method: 'POST',
              body: formData
          })
          .then(response => response.json())
          .then(data => {
              if (data.key) {
                  // Open Razorpay payment gateway
                  const options = {
                      key: data.key,
                      amount: data.amount,
                      currency: data.currency,
                      name: data.name,
                      description: data.description,
                      order_id: data.order_id,
                      handler: function(response) {
                          // Verify payment
                          fetch('/verify_payment', {
                              method: 'POST',
                              headers: {
                                  'Content-Type': 'application/x-www-form-urlencoded',
                              },
                              body: `razorpay_payment_id=${response.razorpay_payment_id}&razorpay_order_id=${response.razorpay_order_id}&razorpay_signature=${response.razorpay_signature}`
                          })
                          .then(verifyResponse => verifyResponse.json())
                          .then(verifyData => {
                              if (verifyData.success) {
                                  alert('Property listed successfully!');
                                  window.location.href = '/';
                              } else {
                                  alert('Payment verification failed');
                              }
                          })
                          .catch(error => {
                              console.error('Error:', error);
                              alert('An error occurred during payment verification');
                          });
                      },
                      prefill: data.prefill,
                      theme: {
                          color: '#3399cc'
                      }
                  };
                  const rzp1 = new Razorpay(options);
                  rzp1.open();
              } else {
                  alert('Error creating payment order');
              }
          })
          .catch(error => {
              console.error('Error:', error);
              alert('An error occurred');
          });
      }
  });
});

// Properties page Authentication : 

// document.addEventListener('DOMContentLoaded', function() {
//     const propertyLink = document.getElementById('property-link');
  
//     if (propertyLink) {
//         propertyLink.addEventListener('click', function(event) {
//             event.preventDefault(); // Prevent the default link behavior
          
//             // Read the data attribute and convert it to boolean
//             const isAuthenticated = propertyLink.getAttribute('data-authenticated') === 'true';
          
//             if (isAuthenticated) {
//                 // Redirect to the properties page
//                 window.location.href = propertyLink.href;
//             } else {
//                 // Redirect to the login page
//                 window.location.href = "{{ url_for('login') }}";
//             }
//         });
//     }
// });




// document.addEventListener('DOMContentLoaded', function () {
//     const slides = document.querySelectorAll('.banner-slide');
//     let currentSlide = 0;

//     function showSlide(index) {
//         slides.forEach((slide, i) => {
//             slide.classList.toggle('active', i === index);
//         });
//     }

//     function nextSlide() {
//         currentSlide = (currentSlide + 1) % slides.length;
//         showSlide(currentSlide);
//     }

//     setInterval(nextSlide, 30000); // Change slide every 30 seconds
// });
