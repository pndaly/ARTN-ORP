# Arizona Robotic Telescope Network Observation Request Portal

Presentation to ARTN Group, Wednesday 27 February 2019 (Phil Daly)


## The Specification

Way back in August 2018, the ARTN group decided on various fields that should be present in 
an observation portal: 

![alt text][logo]

[logo]: images/Email.png "David's Email"

If anyone remembers what QA actually means and how we measure it, please advise.

## The Design

 - A Flask front-end talks to a PostGreSQL back end
 - Database model is a one-to-many relationship (users -> observation requests)
 - 2 levels of accounts (admin, non-admin)
 - 1 admin account per telescope
 - Regular users can submit requests, view them, edit them *etc* but *not* execute them
 - *Only admins can send observations to the telescope*

## Access

We are still thinking about where to host the portal. It needs to be accessible by all
telescopes in the network so options are:

 - scopenet.as.arizona.edu
 - www.as.arizona.edu
 - `<your suggestion here>`

## Registration

Registration is required so we can keep track of who is using the system. However, we provide
demo accounts for those who just want to explore the system:

| Username      | Password      | Is Admin? | Is Disabled? |
|:-------------:|:-------------:|:---------:|:------------:|
| Demo1         | upon request  | No        | No           |
| Demo2         | upon request  | No        | No           |
| Demo3         | upon request  | No        | No           |
| Demo4         | upon request  | No        | No           |
| Demo5         | upon request  | No        | Yes          |

*NB: All demo accounts and observation requests are volatile and can disappear at any time!*

Right now, a new user completes the registration page and is allowed to login. When we have a 
public-facing site, this allows *anyone* the world over to create an account. This is probably not
what we want to do and may violate any university security policy. The preferred option is to
allow registration to be moderated and send an email to the user when the registration is approved.

*Please provide comments on whether we should we allow new registrations with or without verification?*

## Screen Shots

### Landing Page
![alt text][landingpage]

[landingpage]: images/LandingPage.png "Landing Page"


### Registration Page
![alt text][registrationpage]

[registrationpage]: images/RegistrationPage.png "Registration Page"


### Login Page
![alt text][loginpage]

[loginpage]: images/LoginPage.png "Login Page"

The reset password request sends an embedded link in an email to the registered user.

### Disabled Account Page
![alt text][disabledaccount]

[disabledaccount]: images/DisabledAccount.png "Disabled Account Page"

### User (Home) Page
![alt text][userpage]

[userpage]: images/UserPage.png "User Home Page"


### Create Observation Request Page
![alt text][createobservationrequestpage]

[createobservationrequestpage]: images/CreateObservationRequestPage.png "Create Observation Request Page"

Future enhancement: provide a button next to the object name for astropy co-ordinate lookup

### View Observation Requests Page
![alt text][viewobservationrequestspage]

[viewobservationrequestspage]: images/ViewObservationRequestsPage.png "View Observation Requests Page"

Regular users only see their requests. Admin users see *all* requests and can send them to 
the appropriate telescope.

## Icons

![alt text][navbaricons]

[navbaricons]: images/NavBarIcons.png "NavBar Icons"
L-to-R: Landing page, email operator, call operator, help, api, user home page, logout.

![alt text][obsreqicons]

[obsreqicons]: images/ObsReqIcons.png "ObsReq Icons"
L-to-R: observable/non-observable, show detail, delete, edit.

Delete means delete!

## Future

Incorporate hooks for other telescopes in the network
