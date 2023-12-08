import requests
from datetime import datetime, timedelta, timezone
import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(filename='script.log', level=logging.DEBUG)



def get_commits_last_two_weeks(github_username, repo_owner, repo_name, access_token):
    # Calculate the date two weeks ago from today
    two_weeks_ago = datetime.now(timezone.utc) - timedelta(days=14)
    two_weeks_ago_str = two_weeks_ago.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Construct the GitHub API endpoint URL
    api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits'

    # Include access token in the request headers
    headers = {'Authorization': f'token {access_token}'}

    # Make the API request with parameters to filter by date and author
    response = requests.get(api_url, headers=headers, params={'since': two_weeks_ago_str, 'author': github_username})

    # Check for a successful response
    if response.status_code == 200:
        # Parse the response and get the number of commits
        commits = response.json()
        num_commits = len(commits)
        return num_commits
    else:
        # Handle API request errors
        return None


def get_user_commits(username, repo_owner, repo_name, access_token=None):

    page = 1
    num_commits = 0
    
    while True:
        # Construct the GitHub API endpoint URL
        api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits'

        # Optional: Include access token for authenticated requests
        headers = {'Authorization': f'token {access_token}'} if access_token else {}

        # Make the API request with parameters to filter by author and page
        response = requests.get(api_url, headers=headers, params={'author': username, 'page': page})

        # Check for a successful response
        if response.status_code == 200:
            # Parse the response and get the number of commits on this page
            commits = response.json()
            num_commits += len(commits)

            # Check if there are more pages
            if len(commits) < 30:
                break  # No more commits on subsequent pages
            else:
                page += 1  # Move to the next page
        else:
            # Handle API request errors
            return None

    return num_commits
    
    
def get_user_lines_changed(username, repo_owner, repo_name, access_token=None):
    page = 1
    num_lines_changed = 0
    
    while True:
        api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits'

        headers = {'Authorization': f'token {access_token}'} if access_token else {}

        response = requests.get(api_url, headers=headers, params={'author': username, 'page': page})

        if response.status_code == 200:
            commits = response.json()

            for commit in commits:
                commit_sha = commit['sha']
                commit_details = get_commit_details(repo_owner, repo_name, commit_sha, access_token)
                
                if commit_details:
                    num_lines_changed += commit_details['stats']['total']

            if len(commits) < 30:
                break  
            else:
                page += 1  
        else:
            return None

    return num_lines_changed


def get_commit_details(repo_owner, repo_name, commit_sha, access_token=None):
    api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit_sha}'

    headers = {'Authorization': f'token {access_token}'} if access_token else {}

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None
 
 
def insert_metrics_into_mysql(metrics):
    connection = None
    cursor = None
    
    try:
        connection = mysql.connector.connect(
            host='mysql',
            database='GIT_PERF',
            user='root',
            password='root'
        )
        if connection.is_connected():
            logging.info("Connected to MySQL database.")

        else:
            logging.info("Connected to MySQL database.")
        #host='localhost'
        
        cursor = connection.cursor()

        # Assuming you have a table named 'metrics' with columns
        # 'github_username', 'num_commits_last_two_weeks', 'num_user_commits', 'num_lines_changed'
        insert_query = '''
            INSERT INTO metrics (github_username, num_commits_last_two_weeks, num_user_commits, num_lines_changed)
            VALUES (%s, %s, %s, %s)
        '''
        values = (
            metrics['github_username'],
            metrics['num_commits_last_two_weeks'],
            metrics['num_user_commits'],
            metrics['num_lines_changed']
        )

        cursor.execute(insert_query, values)
        connection.commit()
        logging.info("Metrics inserted successfully!")

    except Error as e:
        logging.exception("An error occurred: %s", e)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



def get_statistics(github_username, repo_owner, repo_name, access_token = None):
    num_commits_last_two_weeks = get_commits_last_two_weeks(github_username, repo_owner, repo_name, access_token)
    num_user_commits = get_user_commits(github_username, repo_owner, repo_name, access_token)
    num_lines_changed = get_user_lines_changed(github_username, repo_owner, repo_name, access_token)
    
    if num_commits_last_two_weeks is not None and num_user_commits is not None:
        metrics = {
            'github_username' : github_username,
            'num_commits_last_two_weeks': num_commits_last_two_weeks,
            'num_user_commits': num_user_commits,
            'num_lines_changed' : num_lines_changed
        }
        logging.info("Metrics inserted successfully!!!!!!!!! ***")

        insert_metrics_into_mysql(metrics)
        return {
            'github_username' : github_username,
            'num_commits_last_two_weeks': num_commits_last_two_weeks,
            'num_user_commits': num_user_commits,
            'num_lines_changed' : num_lines_changed, 
            'git_version': 'V2'
        }
    else:
        return None
      
