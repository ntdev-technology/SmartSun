function handleMalfunction(number, reason) {
    console.log(number, reason)
    var malfunctionDiv = document.createElement('div');
    malfunctionDiv.className = 'malfunction-box';

    var malfunctionHeader = document.createElement('p');
    malfunctionHeader.className = 'MalfuncHeader';
    malfunctionHeader.textContent = 'Malfunction - ' + number;

    var malfunctionReason = document.createElement('p');
    malfunctionReason.className = 'MalfuncReason';
    malfunctionReason.innerHTML = "Discription:<br>" + reason;

    var malfunctionAdvice = document.createElement('p');
    malfunctionAdvice.className = 'MalfuncAD';
    malfunctionAdvice.innerHTML = "If this error persists, please contact one of the distributers.";

    var IgnoreBtn = document.createElement('div');
    IgnoreBtn.className = 'malf-ign';
    IgnoreBtn.innerHTML = 'ignore';

    IgnoreBtn.addEventListener('click', function () {
        HandleIgnore();
    });

    malfunctionDiv.appendChild(malfunctionHeader);
    malfunctionDiv.appendChild(malfunctionReason);
    malfunctionDiv.appendChild(malfunctionAdvice);
    malfunctionDiv.appendChild(IgnoreBtn);

    document.body.insertBefore(malfunctionDiv, document.body.firstChild);

    setInterval(function () {
        malfunctionDiv.style.visibility = (malfunctionDiv.style.visibility === 'hidden' ? '' : 'hidden');
    }, 500);

    function HandleIgnore() {
        fetch('/ignore_malf')
        .then(response => {
            console.log(response);
            return response.json();
        })
        .then(data => {
            console.log(data);
        })
        .catch(error => {
            console.error('Error:', error);
        });

        if (malfunctionDiv) {
            malfunctionDiv.parentNode.removeChild(malfunctionDiv);
        }
        window.location.href = '/?state=welcome';
    }
}