document.addEventListener('DOMContentLoaded', function() {
  const startButton = document.getElementById('startButton');
  const stopButton = document.getElementById('stopButton');
  const manualButton = document.getElementById('manualButton');
  const statusMsg = document.getElementById('statusMsg');
  const browseButton = document.getElementById('browseButton');
  const directoryModal = document.getElementById('directoryModal');
  const directoryList = document.getElementById('directoryList');
  const cancelDirSelect = document.getElementById('cancelDirSelect');
  const selectDirBtn = document.getElementById('selectDirBtn');
  const createFolderBtn = document.getElementById('createFolderBtn');
  const newFolderName = document.getElementById('newFolderName');
  
  let selectedDirectory = '';
  
  // Check the status when popup opens
  checkStatus();
  
  startButton.addEventListener('click', function() {
    // Get form values
    const quality = document.getElementById('quality').value;
    const rate = document.getElementById('rate').value;
    const durationMinutes = document.getElementById('duration').value;
    const duration = durationMinutes * 60; // Convert to seconds
    const output = document.getElementById('output').value;
    const name = document.getElementById('name').value;
    
    // Validate inputs
    if (!quality || !rate || !duration || !output) {
      showError('Please fill all required fields');
      return;
    }
    
    // Construct API request to local server
    const url = 'http://localhost:5000/start_capture';
    const params = {
      quality: quality,
      rate: rate,
      duration: duration,
      output: output,
      name: name || null
    };
    
    // Show loading status
    statusMsg.textContent = 'Starting screenshot capture...';
    statusMsg.className = 'status';
    statusMsg.style.display = 'block';
    
    // Send request to local Python server
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        statusMsg.textContent = 'Screenshot capture started successfully!';
        statusMsg.className = 'status success';
        updateButtonVisibility(true);
      } else {
        showError(data.message || 'Failed to start capture');
      }
    })
    .catch(error => {
      showError('Cannot connect to local server. Make sure the Python server is running.');
      console.error('Error:', error);
    });
  });
  
  stopButton.addEventListener('click', function() {
    const url = 'http://localhost:5000/stop_capture';
    const output = document.getElementById('output').value;
    const name = document.getElementById('name').value;
    
    statusMsg.textContent = 'Stopping capture and saving PDF...';
    statusMsg.className = 'status';
    statusMsg.style.display = 'block';
    
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        output: output,
        name: name || null
      }),
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        statusMsg.textContent = 'Capture stopped and PDF saved successfully.';
        statusMsg.className = 'status success';
        updateButtonVisibility(false);
      } else {
        showError(data.message || 'Failed to stop capture');
        checkStatus(); // Double-check status
      }
    })
    .catch(error => {
      showError('Cannot connect to local server. Make sure the Python server is running.');
      console.error('Error:', error);
    });
  });
  
  manualButton.addEventListener('click', function() {
    const quality = document.getElementById('quality').value;
    const url = 'http://localhost:5000/manual_screenshot';
    
    if (!quality) {
      showError('Please select screenshot quality');
      return;
    }
    
    statusMsg.textContent = 'Taking manual screenshot...';
    statusMsg.className = 'status';
    statusMsg.style.display = 'block';
    
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ quality: quality }),
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        statusMsg.textContent = 'Manual screenshot captured successfully!';
        statusMsg.className = 'status success';
      } else {
        showError(data.message || 'Failed to capture manual screenshot');
      }
      
      // Clear message after 3 seconds
      setTimeout(() => {
        statusMsg.style.display = 'none';
      }, 3000);
    })
    .catch(error => {
      showError('Cannot connect to local server. Make sure the Python server is running.');
      console.error('Error:', error);
    });
  });
  
  browseButton.addEventListener('click', function() {
    // Get list of directories
    fetch('http://localhost:5000/recent_directories')
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Clear previous list
          directoryList.innerHTML = '';
          
          // Add each directory as a selectable option
          data.directories.forEach(dir => {
            const dirDiv = document.createElement('div');
            dirDiv.className = 'dirOption';
            dirDiv.textContent = `${dir.name}: ${dir.path}`;
            
            dirDiv.addEventListener('click', function() {
              // Remove selection from all directories
              document.querySelectorAll('.dirOption').forEach(el => {
                el.classList.remove('selected');
              });
              
              // Highlight selected directory
              dirDiv.classList.add('selected');
              selectedDirectory = dir.path;
            });
            
            directoryList.appendChild(dirDiv);
          });
          
          // Show modal
          directoryModal.style.display = 'block';
        } else {
          showError(data.message || 'Failed to get directories');
        }
      })
      .catch(error => {
        showError('Cannot connect to local server. Make sure the Python server is running.');
        console.error('Error:', error);
      });
  });
  
  // Handle cancel button
  cancelDirSelect.addEventListener('click', function() {
    directoryModal.style.display = 'none';
    selectedDirectory = '';
  });
  
  // Handle select button
  selectDirBtn.addEventListener('click', function() {
    if (selectedDirectory) {
      document.getElementById('output').value = selectedDirectory;
      directoryModal.style.display = 'none';
    } else {
      alert('Please select a directory first');
    }
  });
  
  // Handle create folder button
  createFolderBtn.addEventListener('click', function() {
    const folderName = newFolderName.value.trim();
    
    if (!selectedDirectory) {
      alert('Please select a parent directory first');
      return;
    }
    
    if (!folderName) {
      alert('Please enter a folder name');
      return;
    }
    
    fetch('http://localhost:5000/create_directory', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        parent_path: selectedDirectory,
        new_dir_name: folderName
      }),
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Update the input field with the new directory path
        document.getElementById('output').value = data.path;
        directoryModal.style.display = 'none';
        
        // Show success message
        statusMsg.textContent = data.message;
        statusMsg.className = 'status success';
        statusMsg.style.display = 'block';
        
        // Clear after 3 seconds
        setTimeout(() => {
          statusMsg.style.display = 'none';
        }, 3000);
      } else {
        alert(data.message || 'Failed to create directory');
      }
    })
    .catch(error => {
      alert('Cannot connect to local server. Make sure the Python server is running.');
      console.error('Error:', error);
    });
  });
  
  function checkStatus() {
    fetch('http://localhost:5000/status', {
      method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'active') {
        updateButtonVisibility(true);
        statusMsg.textContent = 'A screenshot capture is currently running.';
        statusMsg.className = 'status success';
        statusMsg.style.display = 'block';
      } else {
        updateButtonVisibility(false);
      }
    })
    .catch(error => {
      console.error('Error checking status:', error);
    });
  }
  
  function updateButtonVisibility(isCapturing) {
    if (isCapturing) {
      startButton.style.display = 'none';
      stopButton.style.display = 'block';
    } else {
      startButton.style.display = 'block';
      stopButton.style.display = 'none';
    }
  }
  
  function showError(message) {
    statusMsg.textContent = `Error: ${message}`;
    statusMsg.className = 'status error';
    statusMsg.style.display = 'block';
  }
});