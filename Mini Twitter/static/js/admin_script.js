let accept_user = function(user_id)
{
    fetch('/accept_user/'+user_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        let reviewedContainer = document.querySelector(`#user-row-${user_id} td.user-reviewed`);
        reviewedContainer.innerHTML = "Accepted";
    })
    .catch(error => {
        console.log(error);
    });
}


let reject_user = function(user_id)
{
    let reason = prompt("Please enter a reason for rejecting this user.");
    if (reason == null)
    {
        return;
    }
    fetch('/reject_user/'+user_id, {
        method: 'POST',
        body: JSON.stringify({
            reason: reason
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        let reviewedContainer = document.querySelector(`#user-row-${user_id} td.user-reviewed`);
        reviewedContainer.innerHTML = "Rejected";
    })
    .catch(error => {
        console.log(error);
    });
}


const delete_user = function(user_id)
{
    if (!confirm("Are you sure you want to delete this user?"))
    {
        return;
    }
    fetch('/delete_user/'+user_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        let userContainer = document.querySelector(`#user-row-${user_id}`);
        userContainer.remove();
    })
    .catch(error => {
        console.log(error);
    });

}

const forgive_warning = function(warning_id)
{
    fetch('/forgive_warning/'+warning_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        document.querySelector(`#warning-row-${warning_id} .warning-status`).innerHTML = "Forgiven"
    })
    .catch(error => {
        console.log(error);
    });
}

const close_dispute = function(warning_id)
{
    fetch('/close_dispute/'+warning_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        document.querySelector(`#warning-row-${warning_id} .warning-status`).innerHTML = "Closed"
    })
    .catch(error => {
        console.log(error);
    });
}


const remove_taboo_word = function(word_id)
{
    fetch('/remove_taboo_word/'+word_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        document.querySelector(`#taboo-${word_id}`).remove();
        document.querySelector(`#taboo-hr-${word_id}`).remove();
    })
    .catch(error => {
        console.log(error);
    });
}