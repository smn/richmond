from django.http import HttpResponse

def conversation(request, format):
    if request.method == 'POST':
        yaml_data = request.raw_post_data
        return HttpResponse("OK")
    else:
        response = HttpResponse("Method not allowed")
        response.status_code = 405
        response['Allow'] = 'POST'
        return response
