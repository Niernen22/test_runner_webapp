document.getElementById('RunPlanButton').addEventListener('click', function(event) {
    event.preventDefault();

    const test_id = window.location.pathname.split('/').pop();

    fetch(SCRIPT_ROOT + `/run_test/${test_id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              alert(`Test started successfully! Refresh the page or check the logs for updates. Run ID: ${data.v_run_id}`);

              window.location.href =SCRIPT_ROOT + `/test_steps/${test_id}`;
          } else {
              alert('Error starting test: ' + data.error);
          }
      })
      .catch(error => {
          alert('An unexpected error occurred: ' + error);
      });
});


document.getElementById('ArchiveButton').addEventListener('click', function(event) {
    event.preventDefault();

    const confirmArchive = confirm('Are you sure you want to archive this test plan?');

    if (confirmArchive) {
        document.getElementById('archiveForm').submit();
    }
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.kill-job-btn').forEach(button => {
    button.addEventListener('click', async () => {
      const stepId = button.getAttribute('data-step-id');
      const confirmKill = confirm(`Are you sure you want to kill the job for step ${stepId}?`);
      if (!confirmKill) return;

      try {
        const response = await fetch(`${SCRIPT_ROOT}/kill_job`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ step_id: stepId })
        });

        const result = await response.json();
        alert(result.message);
      } catch (err) {
        console.error(err);
        alert('Error killing job.');
      }
    });
  });
});


document.getElementById('SchedulePlanButton').addEventListener('click', function() {
  document.getElementById('scheduleModal').style.display = 'block';
});

document.getElementById('scheduleCancel').addEventListener('click', function() {
  document.getElementById('scheduleModal').style.display = 'none';
});


document.getElementById('scheduleConfirm').addEventListener('click', function() {
  const test_id = window.location.pathname.split('/').pop();
  const start_time = document.getElementById('scheduleDatetime').value;
  const recurrence = document.getElementById('recurrence').value;

  fetch(SCRIPT_ROOT + `/schedule_test/${test_id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start_time: start_time, recurrence: recurrence })
  })
  .then(response => response.json())
  .then(data => {
      if(data.success){
        alert(`Scheduled successfully!`);
          document.getElementById('scheduleModal').style.display = 'none';
          loadScheduledJobs(); // optional, refresh list under button
      } else {
          alert('Error scheduling test: ' + data.error);
      }
  });
});

function loadScheduledJobs() {
  const pathParts = window.location.pathname.split('/').filter(Boolean);
  const test_id = pathParts[pathParts.length - 1];
  fetch(SCRIPT_ROOT + `/scheduled_jobs/${test_id}`)
      .then(res => res.json())
      .then(jobs => {
          const listDiv = document.getElementById('scheduled-jobs-list');
          listDiv.innerHTML = '';

          const now = new Date();

          jobs.forEach(job => {
              const startTime = job.start_time ? new Date(job.start_time) : null;

              // Only show jobs that are in the future OR recurring
              if ((startTime && startTime >= now) || job.repeat_interval) {
                  const el = document.createElement('div');
                  el.className = 'scheduled-job'; 
                  
                  const text = document.createElement('span');
                  text.textContent = `${job.job_name} - ${job.start_time} - ${job.repeat_interval || 'One-time'}`;

                  const deleteBtn = document.createElement('button');
                  deleteBtn.textContent = '❌';
                  deleteBtn.addEventListener('click', function() {
                      if(confirm('Are you sure you want to delete this scheduled run?')) {
                          fetch(SCRIPT_ROOT + `/delete_scheduled_run/${job.job_name}`, {
                              method: 'POST'
                          }).then(res => res.json())
                            .then(data => {
                                if(data.success) {
                                    alert('Deleted successfully');
                                    loadScheduledJobs(); // refresh list
                                } else {
                                    alert('Error: ' + data.error);
                                }
                            });
                      }
                  });

                  el.appendChild(text);
                  el.appendChild(deleteBtn);
                  listDiv.appendChild(el);
              }
          });
      });
}


document.addEventListener('DOMContentLoaded', () => {
  loadScheduledJobs(); // fetch scheduled jobs when page loads
});
