const like_post = function(post_id)
{
    fetch('/like_post/'+post_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        render_likes(result);
    })
    .catch(error => {
        console.log(error);
    });
}

const dislike_post = function(post_id)
{
    fetch('/dislike_post/'+post_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        render_likes(result);
    })
    .catch(error => {
        console.log(error);
    });
}

const report_post = function(post_id)
{
    fetch('/report_post/'+post_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        show_toast(`post-${post_id}`, "Post reported successfully", "warning");
        hide_report_options(post_id);
    })
    .catch(error => {
        console.log(error);
    });
}

const report_ad = function(post_id)
{
    fetch('/report_ad/'+post_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        show_toast(`post-${post_id}`, "Post reported successfully", "warning");
        hide_report_options(post_id);
    })
    .catch(error => {
        console.log(error);
    });
}

const report_comment = function(comment_id)
{
    fetch('/report_comment/'+comment_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        show_toast(`comment-card-${comment_id}`, "Comment reported successfully", "warning");
        let reportBtn = document.querySelector(`#report-comment-${comment_id}`);
        if(reportBtn)
        {
            reportBtn.remove();
        }
    })
    .catch(error => {
        console.log(error);
    });
}

const follow_user = function(user_id)
{
    fetch('/follow_user/'+user_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        let followButton = document.querySelector(`#follow-${user_id}`);
        let unfollowButton = document.querySelector(`#unfollow-${user_id}`);
        followButton.classList.add("d-none");
        unfollowButton.classList.remove("d-none");
        show_toast(`card-profile-${user_id}`, "User followed", "success", "afterend");
    })
    .catch(error => {
        console.log(error);
    });
}

const unfollow_user = function(user_id)
{
    fetch('/unfollow_user/'+user_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        let followButton = document.querySelector(`#follow-${user_id}`);
        let unfollowButton = document.querySelector(`#unfollow-${user_id}`);
        followButton.classList.remove("d-none");
        unfollowButton.classList.add("d-none");
        show_toast(`card-profile-${user_id}`, "User unfollowed", "danger", "afterend");
    })
    .catch(error => {
        console.log(error);
    });
}

const report_user = function(user_id)
{
    fetch('/report_user/'+user_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        show_toast(`card-profile-${user_id}`, "User reported successfully", "warning");
        let reportBtn = document.querySelector(`#report-profile-${user_id}`);
        if(reportBtn)
        {
            reportBtn.remove();
        }
    })
    .catch(error => {
        console.log(error);
    });
}

const dispute_warning = function(warning_id)
{
    fetch('/dispute_warning/'+warning_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        document.querySelector(`#warning-row-${warning_id} .warning-status`).innerHTML = "Dispute pending"
    })
    .catch(error => {
        console.log(error);
    });
}

const apply_to_job = function(post_id)
{
    fetch('/apply_to_job/'+post_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        show_toast(`post-${post_id}`, "Application sent.", "success");
        let applyButton = document.querySelector(`#post-${post_id} .apply-button button`);
        applyButton.classList.remove("btn-outline-success");
        applyButton.classList.add("btn-success");
        applyButton.classList.add("disabled");
        applyButton.setAttribute("disabled", true);
        applyButton.innerHTML = "Application sent";
    })
    .catch(error => {
        console.log(error);
    });
}

const accept_application = function(application_id, messsage_id)
{
    fetch('/accept_application/'+application_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        // id="application-row-{{application.id}}" class="application-row-for-{{application.message_id}}"
        let allApplications = document.querySelectorAll(`.application-row-for-${messsage_id}`);
        // for each row, except application row remove them
        allApplications.forEach(row => {
            let reviwedCell = row.querySelector(".application-reviewed");
            if(row.id != `application-row-${application_id}`)
            {
                reviwedCell.innerHTML = "Rejected";
            }
            else
            {
                reviwedCell.innerHTML = "Accepted";
            }
        });
    })
    .catch(error => {
        console.log(error);
    });
}

const reject_application = function(application_id, messsage_id)
{
    fetch('/reject_application/'+application_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        let reviwedCell = document.querySelectorAll(`.application-row-${application_id} .application-reviewed`);
        reviwedCell.innerHTML = "Rejected";
    })
    .catch(error => {
        console.log(error);
    });

}

const delete_post = function(post_id)
{
    fetch('/delete_post/'+post_id, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        show_toast(`post-${post_id}`, "Post deleted successfully", "success");
        document.querySelector(`#post-${post_id}`).remove();
    })
    .catch(error => {
        console.log(error);
    });
}

const render_likes = function(post)
{
    const likeCount = document.querySelector(`#post-${post.id} .like-count`);
    const dislikeCount = document.querySelector(`#post-${post.id} .dislike-count`);
    likeCount.innerHTML = `${post.likes}`;
    dislikeCount.innerHTML = `${post.dislikes}`;
    const likeButton = document.querySelector(`#post-${post.id} .like-button button`);
    const dislikeButton = document.querySelector(`#post-${post.id} .dislike-button button`);
    if(post.liked)
    {
        likeButton.classList.remove("btn-outline-primary");
        likeButton.classList.add("btn-primary");
        dislikeButton.classList.remove("btn-danger");
        dislikeButton.classList.add("btn-outline-danger");
    }
    else if(post.disliked)
    {
        likeButton.classList.remove("btn-primary");
        likeButton.classList.add("btn-outline-primary");
        dislikeButton.classList.add("btn-danger");
        dislikeButton.classList.remove("btn-outline-danger");
    }
    else
    {
        likeButton.classList.remove("btn-primary");
        likeButton.classList.add("btn-outline-primary");
        dislikeButton.classList.remove("btn-danger");
        dislikeButton.classList.add("btn-outline-danger");
    }
}

const show_toast = function(before_element_id, message, bg_color="danger", insertType="beforebegin")
{
    let toastHTML = 
    `
        <div id="toast-for-${before_element_id}" class="post-toast show toast align-items-center bg-${bg_color} fw-bold" style="width:100%;" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                        ${message}
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    let existingToast = document.querySelector(`#toast-for-${before_element_id}`);
    if(existingToast)
    {
        existingToast.remove();
    }
    let postItem = document.querySelector(`#${before_element_id}`)
    postItem.insertAdjacentHTML(insertType, toastHTML);
}

const hide_report_options = function(post_id)
{
    let reportBtn = document.querySelector(`#report-${post_id}`);
    if(reportBtn)
    {
        reportBtn.remove();
    }
    let reportAdBtn = document.querySelector(`#report-ad-${post_id}`);
    if(reportAdBtn)
    {
        reportAdBtn.remove();
    }
}