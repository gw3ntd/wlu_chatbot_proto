function setActionForm(action){
    let form = document.getElementById("auth-form");
    if (action === 'web_routes.login'){
        form.action = "{{url_for('web_routes.login')}}";
        form.method = "post";
        form.submit();
}}