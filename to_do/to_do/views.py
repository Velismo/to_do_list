#views.py
from rest_framework.views import APIView
from rest_framework.response import Response

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
    permission_classes = (IsAutheticated,)

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