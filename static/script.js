let lastPrediction = null;

function predictJob() {
    let text = jobText.value;
    fetch("/predict", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({text})
    })
    .then(r=>r.json())
    .then(d=>{
        lastPrediction=d;
        result.innerHTML=`<h3 style="color:${d.prediction=="Fake"?"red":"green"}">
        ${d.prediction} (${d.confidence}%)
        </h3>`;
    });
}

function flagPost(){
    if(!lastPrediction) return alert("Predict first");
    fetch("/flag",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            text:jobText.value,
            prediction:lastPrediction.prediction,
            confidence:lastPrediction.confidence,
            reason:"User flagged"
        })
    }).then(()=>alert("Flagged"));
}

function clearAll(){
    jobText.value="";
    result.innerHTML="";
}

function goDashboard(){
    location.href="/login";
}

function login(){
    fetch("/do_login",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            username:user.value,
            password:pass.value
        })
    })
    .then(r=>r.json())
    .then(d=>{
        if(d.success) location.href="/dashboard";
        else alert("Invalid login");
    });
}
function simulateRetraining() {
    const overlay = document.getElementById('retrainOverlay');
    const progress = document.getElementById('retrainProgress');
    overlay.style.display = 'flex';
    
    let percent = 0;
    const interval = setInterval(() => {
        percent += Math.floor(Math.random() * 15) + 5;
        if (percent >= 100) {
            percent = 100;
            clearInterval(interval);
            setTimeout(() => {
                overlay.style.display = 'none';
                alert('Model Retraining Complete!\nNew Model: LR-v1.0.5\nAccuracy Improvement: +0.42%');
                location.reload();
            }, 500);
        }
        progress.innerText = `Updating Weights: ${percent}%`;
    }, 400);
}
// CHART 1: NEON LOADING DOUGHNUT
const ctx1 = document.getElementById('distributionChart').getContext('2d');

new Chart(ctx1, {
    type: 'doughnut',
    data: {
        labels: ['Fake', 'Real'],
        datasets: [{
            data: [{{ fake }}, {{ real }}],
            backgroundColor: [
                'rgba(239, 68, 68, 0.8)', // Neon Red
                'rgba(34, 197, 94, 0.8)'  // Neon Green
            ],
            borderColor: ['#ef4444', '#22c55e'],
            borderWidth: 2,
            hoverOffset: 20,
            borderRadius: 5, // Gives the segments rounded ends
            spacing: 5       // Adds a small gap between segments
        }]
    },
    options: {
        cutout: '80%',
        responsive: true,
        maintainAspectRatio: false,
        // THE 0-360 LOADING EFFECT
        animation: {
            duration: 2500,     // Time in ms
            easing: 'easeInOutQuart'
        },
        // This makes it start from 0 and go to 360
        transitions: {
            active: { animation: { duration: 500 } }
        },
        plugins: {
            legend: {
                display: true,
                position: 'bottom',
                labels: { color: '#94a3b8', font: { weight: 'bold' } }
            }
        }
    }
});
function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Trigger count-up animation for the stats
window.onload = () => {
    const totalDisplay = document.querySelector('.chart-center-label strong');
    if(totalDisplay) animateValue(totalDisplay, 0, {{ total }}, 2000);
};