#views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.validators import validate_email
from . import utils
import jwt
from django.core.exceptions import ObjectDoesNotExist
from .models import Task, TaskList, ListAccess
from .authentication import ToDoTokenAuthentication

class HelloWorld(APIView):
    def get(self, request):
        return Response('HELLO WORLD from Django.')


# View class to register user
class Register(APIView):
    def post(self, request):
        # The order of required params is important as they are used to setvariables by index
        required_params = ['username', 'password', 'email']
        try:
            data = request.data
            # Checking if all the required parameters are available in data
            if all(key in data for key in required_params):
                try:
                    user_name = self.validate_required_input(required_params[0], data[required_params[0]])
                    password = self.validate_required_input(required_params[1], data[required_params[1]])
                    email = self.validate_required_input(required_params[2], data[required_params[2]])
                except ValidationError as er:
                    return Response({"error": str(er.messages[0])}, status=status.HTTP_400_BAD_REQUEST)


                # Input is now considered valid
                # Creating user object to store in db
                new_user = User()
                new_user.username = user_name
                new_user.password = make_password(password)
                new_user.email = email

                # Trying to setup optional parameters if available
                try:
                    new_user.first_name = data['firstname'] if data['firstname'] is not None else ""
                except KeyError:
                    print("Error while parsing firstname ")
                try:
                    new_user.last_name = data['lastname'] if data['lastname'] is not None else ""
                except KeyError:
                    print("Error while parsing lastname ")

                new_user.save()

                return Response({"status": "Success"}, status=status.HTTP_201_CREATED)

            else:
                return Response({"error": "Required param(s) missing, Please include and retry again"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as exp:
            print("Unexpected exception ocurred: "+str(exp))
            return Response({"error": "Unexpected error occurred, please report this to Admin"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class Login(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request):
        access_token, refresh_token = utils.generate_tokens(request.user)

        if access_token is None or refresh_token is None:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = {
            'access_token': access_token,
            'expires_in': 3600,
            'token_type': "bearer",
            'refresh_token': refresh_token
        }

        return Response(response)

class LoginRefresh(APIView):
    def post(self, request):
        try:
            data = request.data
            try:
                refresh_token = data['refresh_token']
            except KeyError:
                return Response({"error": "Refresh token required!"}, status=status.HTTP_400_BAD_REQUEST)

            # Validating the refresh token
            try:
                decoded_refresh_token_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms='HS256')
            except jwt.exceptions.InvalidSignatureError:
                return Response({"error": "Invalid Signature, Token tampered"}, status=status.HTTP_400_BAD_REQUEST)
            except jwt.exceptions.ExpiredSignatureError:
                return Response({"error": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)
            except (jwt.exceptions.InvalidTokenError, jwt.exceptions.DecodeError):
                return Response({"error": "Invalid Token"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                if not (decoded_refresh_token_payload['type'] == "refresh"):
                    return Response({"error": "Invalid Token type"}, status=status.HTTP_400_BAD_REQUEST)

                user_name = decoded_refresh_token_payload['username']
            except KeyError:
                return Response({"error": "Token Tampered!"}, status=status.HTTP_400_BAD_REQUEST)

            #Getting user object from database
            try:
                current_user = User.objects.get(username=user_name)
            except User.DoesNotExist:
                return Response({"error": "User Doesn't exist"}, status=status.HTTP_400_BAD_REQUEST)
            except User.MultipleObjectsReturned:
                return Response({"error": "Fatal! Multiple users with the same user name exist"}, status=status.HTTP_400_BAD_REQUEST)

            # Generating tokens
            access_token, refresh_token = utils.generate_tokens(current_user)

            if access_token is None or refresh_token is None:
                return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            response = {
                'access_token': access_token,
                'expires_in': 3600,
                'token_type': 'bearer',
                'refresh_token': refresh_token
            }

            return Response(response)

        except Exception as er:
            print(er)
            return Response("Oops!, something went wron whiile handling your request", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListAdd(APIView):
    authentication_classes = (ToDoTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request):
        if request.data.get('name', None) and request.data.get('name') != '':
            # Getting request data
            name = request.data.get('name')
            description = request.data.get('description') if request.data.get('description', None) else ''

            # Writing to database
            try:
                new_list = TaskList(name=name, description=desecription)
                new_list.save()
                new_list_access = ListAccess(user=request.user, list=new_list, role='owner')
                new_list_access.save()

                # Responding back
                resp_dict = {
                    'status': 'success',
                    'message': 'List created succesfully',
                    'data': {
                        'id': new_list.id,
                        'name': new_list.name,
                        'description': new_list.description
                    }
                }
                resp = Response()
                resp.status_code = 201
                resp.data = resp_dict
            except ValueError as val_err:
                # Responding back
                resp_dict = {
                    'status': 'failed',
                    'message': 'Something unexpected happened!, {0}'.format(val_err),
                    'data': {}
                }
                resp = Response()
                resp.status_code = 400
                resp.data = resp_dict
            except Exception as er:
                # Responding back
                resp_dict = {
                    'status': 'failed',
                    'message': 'Something unexpected happened, {0}'.format(er),
                    'data': {}
                }
                resp = Response()
                resp.status_code = 400
                resp.data = resp_dict
        else:
            resp_dict = {
                'status': 'failed',
                'message': 'List name is required but not provided',
                'data': {}
            }
            resp = Response()
            resp.status_code = 400
            resp.data = resp_dict

        return resp


class ListFetch(APIView):
    authentication_classes = (ToDoTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        resp_dict = {
            'status': '',
            'message': '',
            'data': None
        }

        try:
            list_ids = ListAccess.objects.values_list('list').filter(user=request.user)
            lists = TaskList.objects.filter(id_in=list_ids).values()
            resp_dict['status'] = 'success'
            resp_dict['message'] = 'Retrieved the list of todo lists'
            resp_dict['data'] = lists

        except Exception as e:
            print(e)
            resp_dict['status'] = 'Failed'
            resp_dict['message'] = 'SOmething went wrong while fetching data. Error: '+e.__str__()

        return Response(resp_dict)


class TaskAdd(APIView):
    authetication_classes = (ToDoTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        resp_dict = {
            'status': None,
            'message': None,
            'data': None
        }

        req_list_id = request.data.get("list_id")
        req_task_name = request.data.get("name")
        req_task_desc = request.data.get('description') if request.data.get('description', None) else ''

        if req_list_id and TaskList.objects.filter(id=req_list_id).exists() and \
                req_task_name and req_task_name != '':
            try:
                task_list = TaskList.objects.get(id=req_list_id)

                user_perm = ListAccess.objects.filter(user=request.user, list=task_list)

                if user_perm.count() != 1 or user_perm.first().role != 'owner':
                    raise PermissionError("You do not have permissions to edit this list")
                new_task = Task(name=req_task_name, list=task_list, description=req_task_desc)
                new_task.save()

                resp_dict['status'] = 'success'
                resp_dict['message'] = 'Task creation successful'
                resp_dict['data'] = {
                    "name": new_task.name, 
                    "description": new_task.description, 
                    "done": new_task.done, 
                    "list_id": new_task.list.id
                    }

            except PermissionError as pe:
                resp_dict['status'] = "failed"
                resp_dict['message'] = pe.__str__()
                resp_dict['data'] = None
                resp = Response(resp_dict)
                resp.status_code = 403
            except Exception as e:
                resp_dict['status'] = 'failed'
                resp_dict['message'] = "Something went wrong. Error: "+e.__str__()
                resp_dict['data'] = None
                resp = Response(resp_dict)
                resp.status_code = 500
        else:
            resp_dict['status'] = "failed"
            resp_dict['message'] = "Invalida name or list_id passed"
            resp_dict['data'] = None
            resp = Response(resp_dict)
            resp.status_code = 400

        return resp


class TaskFetch(APIView):
    authentication_classes = (ToDoTokenAuthentication,)
    permission_Classes = (IsAuthenticated,)

    def get(self, request):

        resp_dict = {
            'status': None,
            'message': None,
            'data': None
        }

        try:
            list_id = request.query_params.get("list_id", None)

            # Checking if the list id is provided
            if list_id is None or list_id == '':
                raise ValueError("Invlaid list_id")

            # Fetching list object
            try:
                task_list_obj = TaskList.objects.get(id=list_id)
            except ObjectDoesNotExist:
                raise ValueError("Invalid list_id")

            #checking if the user on the given list
            try:
                list_perm_qs = ListAccess.objects.get(user=request.user, list=task_list_obj)
            except ObjectDoesNotExist:
                raise PermissionError("You do not have permission to access this list")

            # fetching task
            tasks = Task.objects.filter(list=task_list_obj).values()

            resp_dict['status'] = 'success'
            resp_dict['message'] = 'Fetched task successfully'
            resp_dict['data'] = tasks
            resp = Response(resp_dict)
            resp.status_code = 200

        except PermissionError as pe:
            resp_dict['status'] = 'failed'
            resp_dict['message'] = pe.__str__()
            resp_dict['data'] = None
            resp = Response(resp_dict)
            resp.status_code = 403

        except ValueError as ve:
            resp_dict['status'] = 'failed'
            resp_dict['message'] = ve.__str__()
            resp_dict['data'] = None
            resp = Response(resp_dict)
            resp.status_code = 400

        except Exception as e:
            resp_dict['status'] = 'failed'
            resp_dict['message'] = "Something went wrong. Error: "+e.__str__()
            resp_dict['data'] = None
            resp = Response(resp_dict)
            resp.status_code = 500

        return resp


