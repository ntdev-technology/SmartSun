document.addEventListener('DOMContentLoaded', function () {
  const notCon = document.getElementById('notCon');

  function createNotification(message) {
    console.log(message)
    const notification = document.createElement('div');
    notification.classList.add('notification')

    notification.classList.add('defNot');
      
    const text = document.createElement('div');
    text.innerHTML = message.replace('\n', '<br>');

    const closeBtn = document.createElement('div');
    closeBtn.className = 'notification-close';
    closeBtn.innerHTML = '&nbsp&times&nbsp';

    closeBtn.addEventListener('click', function () {
      notCon.removeChild(notification);
      adjustNotificationPositions();
    });

    notification.appendChild(text);
    notification.appendChild(closeBtn);
    notCon.appendChild(notification);

    adjustNotificationPositions();
  }

  function adjustNotificationPositions() {
    const notifications = document.getElementsByClassName('notification');
    let topOffset = 10;

    for (let i = 0; i < notifications.length; i++) {
        notifications[i].style.top = topOffset + 'px';
        topOffset += notifications[i].offsetHeight + 10;
    }
  }


  function get_flashed_messages() {
    fetch('/flash-messages', {
      method: "GET",
      cache: "no-cache",
    headers: {
      "Content-Type": "application/json",
      "with-categories": true
    }
    }).then(response => { return response.json()
    }).then(data => {
      console.log(data)
      for (var not of data){
          console.log(not.message)
          createNotification(not.message)
        }
    }).catch(err => console.error(err)
    )
  }

  get_flashed_messages();
  
});