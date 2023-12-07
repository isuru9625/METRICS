from flask import Flask, request, jsonify
import statistics_service

app = Flask(__name__)

@app.route('/get_statistics', methods=['GET'])
def get_statistics():
    # Get parameters from the query string or request data
    github_username = request.args.get('github_username', default=None)
    repository_owner = request.args.get('repository_owner', default=None)
    repository_name = request.args.get('repository_name', default=None)
    access_token = request.args.get('access_token', default=None)

    if None in [github_username, repository_owner, repository_name, access_token]:
        return jsonify({'error': 'Missing required parameters'}), 400

    stats = statistics_service.get_statistics(github_username, repository_owner, repository_name, access_token)

    if stats is not None:
        return jsonify(stats)
    else:
        return jsonify({'error': 'Failed to fetch commit information'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0' , debug=True)
