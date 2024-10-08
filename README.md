# Social Media Application - Implementation of twitter

This project is a social media application that allows users to manage their profiles, post tweets, follow other users, and view a timeline of tweets. The application uses **Firebase** for authentication, data storage, and real-time updates.

## Features

- **Login/Logout Service**: Implements Firebase authentication using `firebase-login.js`. The login system must match the provided examples.
- **Firestore Collections**:
  - **User**: Represents users of the application.
  - **Tweet**: Represents tweets posted by users. Each tweet is linked to one user and includes fields `username` (string) and `date` (datetime). A composite index is set on `username` (ascending) and `date` (descending).
- **Unique Username Setup**: On the first login, users are prompted to set a unique username.
- **Tweet Addition**: Users can add tweets up to 140 characters in length.

- **Username Search**: Search functionality to find usernames matching the beginning of the input.
- **Tweet Content Search**: Search functionality to find tweets based on the beginning of their content.
- **User Profile Page**: Displays basic user information, their last 10 tweets, and includes a button to follow or unfollow the user.
- **Follow User**: Users can start following other users.

- **Unfollow User**: Users can stop following other users.
- **Timeline Generation**: Displays the last 20 tweets from the user’s following list in reverse chronological order, including the user’s own tweets.
- **Edit Tweet**: Allows users to edit their tweets.

- **Delete Tweet**: Users can delete their tweets.
- **Image Upload**: Users can upload images (jpg/png) to cloud storage and link them to tweets. Images can also be updated when editing a tweet.
- **UI Design**: Well-designed, intuitive UI for ease of use.

## Technologies Used

- **Firebase Authentication** for login/logout
- **Firestore** for data storage
- **Firebase Storage** for image uploads
- **HTML/CSS/JavaScript** for frontend development
- **Firebase SDK** for database interactions and real-time updates


