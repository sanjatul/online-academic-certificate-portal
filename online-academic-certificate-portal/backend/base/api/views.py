from datetime import date

import requests
from base.models import (ProvisionalCertificate, Student, StudentResult, User,
                         testTable)
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from jwt import ExpiredSignatureError, decode, encode, exceptions
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .helpers import save_pdf
from .permissions import isChairmanUser, isStudentUser
from .serializers import (LoginSerializer, ProvisionalCertificateSerializer,
                          UserSerializer, chairmanSignupSerializer,
                          emailChangeSerializer, studentSignupSerializer,
                          testSerializer)

# from .utils import Util


class chairmanSignupView(generics.GenericAPIView):
    serializer_class = chairmanSignupSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        user_data = User.objects.get(email=serializer.data['email'])

        token = encode({'id': user_data.id},
                       settings.SECRET_KEY, algorithm='HS256')
        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')
        absurl = 'http://' + current_site + \
            relative_link + "?token=" + str(token)

        html_message = render_to_string('registration_confirm.html', {
            'fullname': user_data.fullname,
            'confirmationUrl': absurl
        })
        plain_message = strip_tags(html_message)
        send_mail(
            "email confirmation for NSTU ODPP",
            plain_message,
            "souravdebnath97@gmail.com",
            [user_data.email],
            html_message=html_message
        )

        return Response(
            {
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "message": "account created successfully",
            }
        )


class studentSignupView(generics.GenericAPIView):
    serializer_class = studentSignupSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        user_data = User.objects.get(email=serializer.data['email'])

        token = encode({'id': user_data.id},
                       settings.SECRET_KEY, algorithm='HS256')
        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')
        absurl = 'http://' + current_site + \
            relative_link + "?token=" + str(token)

        html_message = render_to_string('registration_confirm.html', {
            'fullname': user_data.fullname,
            'confirmationUrl': absurl
        })
        plain_message = strip_tags(html_message)
        send_mail(
            "email confirmation for NSTU ODPP",
            plain_message,
            "souravdebnath97@gmail.com",
            [user_data.email],
            html_message=html_message
        )

        return Response(
            {
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                # "token": Token.objects.get(user=user).key,
                "message": "account created successfully",
            }
        )


class VerifyEmail(generics.GenericAPIView):

    @staticmethod
    def get(request):
        token = request.GET.get('token')
        try:
            payload = decode(token, settings.SECRET_KEY, algorithms='HS256')
            user = User.objects.get(id=payload['id'])
            if user.email_validation is False:
                user.email_validation = True
                user.save()
            return redirect("http://localhost:3000/login")

        except ExpiredSignatureError:
            return Response({'message': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)

        except exceptions.DecodeError:
            return Response({'message': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)


class customAuthToken(generics.GenericAPIView):

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key
        })


class LogoutView(APIView):
    def post(self, request, format=None):
        request.auth.delete()
        return Response(status=status.HTTP_200_OK)


class studentOnlyView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated & isStudentUser]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class chairmanOnlyView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated & isChairmanUser]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class continuousVerificationView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class emailChangeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = emailChangeSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            user_data = User.objects.get(email=serializer.data['oldEmail'])

            token = encode({'id': user_data.id},
                           settings.SECRET_KEY, algorithm='HS256')

            current_site = get_current_site(request).domain
            relative_link = reverse('emailchange-verify')
            absurl = 'http://' + current_site + \
                relative_link + "?token=" + str(token)

            html_message = render_to_string('registration_confirm.html', {
                'fullname': user_data.fullname,
                'confirmationUrl': absurl
            })
            plain_message = strip_tags(html_message)
            send_mail(
                "email confirmation for NSTU ODPP",
                plain_message,
                "souravdebnath97@gmail.com",
                [user_data.new_email],
                html_message=html_message
            )

            return Response({'message': 'done', "user": UserSerializer(user, context=self.get_serializer_context()).data, }, status=status.HTTP_200_OK)

        except:
            return Response({
                "message": "Your username has not there"
            }, status=status.HTTP_400_BAD_REQUEST)


class emailChangeVerifyView(generics.GenericAPIView):

    @staticmethod
    def get(request):
        token = request.GET.get('token')
        try:
            payload = decode(token, settings.SECRET_KEY, algorithms='HS256')
            user = User.objects.get(id=payload['id'])
            user.email = user.new_email

            if user.new_email_validation is False:
                user.new_email_validation = True
                user.save()

            return redirect("http://localhost:3000/login")

        except ExpiredSignatureError:
            return Response({'message': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)

        except exceptions.DecodeError:
            return Response({'message': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)


# <---- Provisional certifiate applied all list ---->

@api_view(["GET"])
def getProvisionalCertificateAppliedList(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True)
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)

# <---- Provisional certifiate applied details view ---->


@api_view(["GET"])
def getProvisionalCertificateAppliedDetails(request, roll):

    studentResult = StudentResult.objects.get(roll=roll)
    student = ProvisionalCertificate.objects.get(result=studentResult)
    serializedStudents = ProvisionalCertificateSerializer(student, many=False)
    return Response(serializedStudents.data)


# <---- Student Applying for Provisional certifiate ---->

@api_view(["POST"])
def applyProvisional(request):
    applied_email = request.data['email']
    student = Student.objects.get(email=applied_email)
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.is_applied == False:
        provisionalCertificateDetails.is_applied = True
        provisionalCertificateDetails.save()
        return Response({'message': 'successfully applied for provitional'}, status=status.HTTP_200_OK)

    else:
        return Response({'message': 'already applied'}, status=status.HTTP_400_BAD_REQUEST)


# <---- Student Paying for Provisional certifiate ---->

@api_view(["POST"])
def payProvisional(request):
    applied_email = request.data['email']
    student = Student.objects.get(email=applied_email)
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.is_paid == False:
        provisionalCertificateDetails.is_paid = True
        provisionalCertificateDetails.save()
        return Response({'message': 'successfully paid for provitional'}, status=status.HTTP_200_OK)

    else:
        return Response({'message': 'already paid'}, status=status.HTTP_400_BAD_REQUEST)
# <---- Student uploading image for Provisional certifiate ---->


@api_view(["GET"])
def uploadSscCertificate(request):
    try:
        applied_email = request.data['email']
        ssc_certificate = request.data['ssc_certificate']
        student = Student.objects.get(email=applied_email)
        provisionalCertificateDetails = ProvisionalCertificate.objects.get(
            student_details=student)
        provisionalCertificateDetails.ssc_certificate = ssc_certificate
        provisionalCertificateDetails.save()
        return Response({'message': 'successfully uploaded'}, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'something went wrong'}, status=status.HTTP_400_BAD_REQUEST)


# <---- Provisional certifiate applied all list for chairman ---->


@api_view(["GET"])
def getProvisionalAppliedListforChairman(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, chairman_status__isnull=True, provost_status__isnull=True, librarian_status__isnull=True, examController_status__isnull=True)
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)


# <---- Provisional certifiate accepted list by chairman ---->

@api_view(["GET"])
def getProvisionalAcceptedListbyChairman(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, chairman_status="approved")
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)

# <---- Provisional certifiate rejected list by chairman ---->


@api_view(["GET"])
def getProvisionalRejectedListbyChairman(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, chairman_status="rejected")
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)


# <---- Chairman accepting for Provisional certifiate ---->


@api_view(["POST"])
def chairmanAcceptProvisional(request):
    student_email = request.data['student_email']
    student = Student.objects.get(email=student_email)
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.chairman_status != 'approved':
        provisionalCertificateDetails.chairman_status = 'approved'
        provisionalCertificateDetails.chairman_action_date = date.today()
        provisionalCertificateDetails.save()
        return Response({'message': 'successfully accepted provitional'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'already accepted this student'}, status=status.HTTP_400_BAD_REQUEST)


# <---- Chairman Rejecting for Provisional certifiate ---->

@api_view(["POST"])
def chairmanRejectProvisional(request):
    student_email = request.data['student_email']
    message = request.data['message']
    student = Student.objects.get(email=student_email)
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.chairman_status != 'rejected':
        provisionalCertificateDetails.chairman_status = 'rejected'
        provisionalCertificateDetails.chairman_action_date = date.today()
        provisionalCertificateDetails.save()
        html_message = render_to_string('certificate_reject.html', {
            'fullname': student.name,
            'message': message
        })
        plain_message = strip_tags(html_message)
        send_mail(
            "Chairman Rejection for NSTU ODPP",
            plain_message,
            "souravdebnath97@gmail.com",
            ['souravdebnath10@gmail.com'],
            html_message=html_message
        )
        return Response({'message': 'successfully rejected provitional'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'already rejected this student'}, status=status.HTTP_400_BAD_REQUEST)

# ---------------!-------------------

# <---- Provisional certifiate applied all list for provost ---->


@api_view(["GET"])
def getProvisionalAppliedListforProvost(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, chairman_status="approved", provost_status__isnull=True, librarian_status__isnull=True, examController_status__isnull=True)
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)


# <---- Provisional certifiate accepted list by provost ---->

@api_view(["GET"])
def getProvisionalAcceptedListbyProvost(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, chairman_status="approved", provost_status="approved")
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)

# <---- Provisional certifiate rejected list by provost ---->


@api_view(["GET"])
def getProvisionalRejectedListbyProvost(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, provost_status="rejected")
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)


# <---- provost accepting for Provisional certifiate ---->


@api_view(["POST"])
def provostAcceptProvisional(request):
    student_email = request.data['student_email']
    student = Student.objects.get(email=student_email)
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.provost_status != 'approved':
        provisionalCertificateDetails.provost_status = 'approved'
        provisionalCertificateDetails.provost_action_date = date.today()
        provisionalCertificateDetails.save()
        return Response({'message': 'successfully accepted provitional'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'already accepted this student'}, status=status.HTTP_400_BAD_REQUEST)


# <---- provost Rejecting for Provisional certifiate ---->

@api_view(["POST"])
def provostRejectProvisional(request):
    student_email = request.data['student_email']
    message = request.data['message']
    student = Student.objects.get(email=student_email)
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.provost_status != 'rejected':
        provisionalCertificateDetails.provost_status = 'rejected'
        provisionalCertificateDetails.provost_action_date = date.today()
        provisionalCertificateDetails.save()
        html_message = render_to_string('certificate_reject.html', {
            'fullname': student.name,
            'message': message
        })
        plain_message = strip_tags(html_message)
        send_mail(
            "Provost Rejection for NSTU ODPP",
            plain_message,
            "souravdebnath97@gmail.com",
            ['souravdebnath10@gmail.com'],
            html_message=html_message
        )
        return Response({'message': 'successfully rejected provitional'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'already rejected this student'}, status=status.HTTP_400_BAD_REQUEST)


# ---------------!-------------------

# <---- Provisional certifiate applied all list for librarian ---->


@api_view(["GET"])
def getProvisionalAppliedListforLibrarian(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, chairman_status="approved", provost_status="approved", librarian_status__isnull=True, examController_status__isnull=True)
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)


# <---- Provisional certifiate accepted list by Librarian ---->

@api_view(["GET"])
def getProvisionalAcceptedListbyLibrarian(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, chairman_status="approved", provost_status="approved", librarian_status="approved")
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)

# <---- Provisional certifiate rejected list by Librarian ---->


@api_view(["GET"])
def getProvisionalRejectedListbyLibrarian(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, librarian_status="rejected")
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)


# <---- Librarian accepting for Provisional certifiate ---->


@api_view(["POST"])
def librarianAcceptProvisional(request):
    student_email = request.data['student_email']
    student = Student.objects.get(email=student_email)
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.librarian_status != 'approved':
        provisionalCertificateDetails.librarian_status = 'approved'
        provisionalCertificateDetails.librarian_action_date = date.today()
        provisionalCertificateDetails.save()
        return Response({'message': 'successfully accepted provitional'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'already accepted this student'}, status=status.HTTP_400_BAD_REQUEST)


# <---- Librarian Rejecting for Provisional certifiate ---->

@api_view(["POST"])
def librarianRejectProvisional(request):
    student_email = request.data['student_email']
    message = request.data['message']
    student = Student.objects.get(email=student_email)
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.librarian_status != 'rejected':
        provisionalCertificateDetails.librarian_status = 'rejected'
        provisionalCertificateDetails.librarian_action_date = date.today()
        provisionalCertificateDetails.save()
        html_message = render_to_string('certificate_reject.html', {
            'fullname': student.name,
            'message': message
        })
        plain_message = strip_tags(html_message)
        send_mail(
            "Librarian Rejection for NSTU ODPP",
            plain_message,
            "souravdebnath97@gmail.com",
            ['souravdebnath10@gmail.com'],
            html_message=html_message
        )
        return Response({'message': 'successfully rejected provitional'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'already rejected this student'}, status=status.HTTP_400_BAD_REQUEST)


# ---------------!-------------------

# <---- Provisional certifiate applied all list for exam controller ---->


@api_view(["GET"])
def getProvisionalAppliedListforExamController(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, chairman_status="approved", provost_status="approved", librarian_status="approved", examController_status__isnull=True)
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)


# <---- Provisional certifiate accepted list by Exam Controller ---->

@api_view(["GET"])
def getProvisionalAcceptedListbyExamController(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, chairman_status="approved", provost_status="approved", librarian_status="approved", examController_status="approved")
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)

# <---- Provisional certifiate rejected list by Exam Controller ---->


@api_view(["GET"])
def getProvisionalRejectedListbyExamController(request):
    students = ProvisionalCertificate.objects.filter(
        is_applied=True, is_paid=True, examController_status="rejected")
    serializedStudents = ProvisionalCertificateSerializer(students, many=True)
    return Response(serializedStudents.data)


# <---- Exam Controller accepting for Provisional certifiate ---->


@api_view(["POST"])
def examControllerAcceptProvisional(request):
    student_email = request.data['student_email']
    checkedBy = request.data['checkedBy']
    issued_date = request.data['issued_date']
    student = Student.objects.get(email=student_email)
    student_result = StudentResult.objects.get(student_details=student)
    student_department = student.department
    student_roll = student.roll
    student_cgpa = student_result.cgpa
    student_roll_removed_last = student_roll.rstrip(student_roll[-1])
    serial_number = "NSTU/REG/"+student_department + \
        "/provisional/"+student_roll_removed_last[3:]
    blockchain_data = {"roll": student_roll+"-provisional",
                       "certificate_number": serial_number, "cgpa": student_cgpa}
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.examController_status != 'approved':
        provisionalCertificateDetails.examController_status = 'approved'
        provisionalCertificateDetails.checkedBy = checkedBy
        provisionalCertificateDetails.issued_date = issued_date
        provisionalCertificateDetails.serial_number = serial_number
        provisionalCertificateDetails.examController_action_date = date.today()
        provisionalCertificateDetails.save()
        response = requests.post(
            'http://localhost:3000/create', json=blockchain_data)
        print(response.json())
        return Response({'message': 'successfully accepted provitional'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'already accepted this student'}, status=status.HTTP_400_BAD_REQUEST)


# <---- Exam Controller Rejecting for Provisional certifiate ---->

@api_view(["POST"])
def examControllerRejectProvisional(request):
    student_email = request.data['student_email']
    message = request.data['message']
    student = Student.objects.get(email=student_email)
    provisionalCertificateDetails = ProvisionalCertificate.objects.get(
        student_details=student)
    if provisionalCertificateDetails.examController_status != 'rejected':
        provisionalCertificateDetails.examController_status = 'rejected'
        provisionalCertificateDetails.examController_action_date = date.today()
        provisionalCertificateDetails.save()
        html_message = render_to_string('certificate_reject.html', {
            'fullname': student.name,
            'message': message
        })
        plain_message = strip_tags(html_message)
        send_mail(
            "Exam Controller Rejection for NSTU ODPP",
            plain_message,
            "souravdebnath97@gmail.com",
            ['souravdebnath10@gmail.com'],
            html_message=html_message
        )
        return Response({'message': 'successfully rejected provitional'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'already rejected this student'}, status=status.HTTP_400_BAD_REQUEST)


# <---- pdf test api ---->
class GeneratePdf(APIView):
    def post(self, request):
        student_email = request.data['student_email']

        student = Student.objects.get(email=student_email)

        provisionalCertificateDetails = ProvisionalCertificate.objects.get(
            student_details=student)
        params = {
            'hello': 'hello'
        }
        file_name, status = save_pdf(params)
        if not status:
            return Response({'status': 400})
        url = "127.0.0.1:8000/media/certificate/"+str(file_name)+".pdf"

        provisionalCertificateDetails.provisional_certificate_url = url
        provisionalCertificateDetails.save()

        return Response({'status': 200, 'path': f'/media/certificate/{file_name}.pdf'})
# <---- test api ---->


@api_view(["POST"])
def testApi(request, pk):
    print('req: ', request.data['subject'])
    testData = testTable.objects.get(id=pk)
    testData.subject = request.data['subject']
    testData.save()
    serializedData = testSerializer(testData, many=False)
    return Response(serializedData.data)
