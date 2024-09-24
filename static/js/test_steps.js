document.getElementById('RunPlanButton').addEventListener('click', function(event) {
    event.preventDefault();

    const test_id = window.location.pathname.split('/').pop();
    
    fetch(`/run_test/${test_id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).finally(() => {
        window.location.href = `/test_steps/${test_id}`;
    });
});
