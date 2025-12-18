#include <iostream>
#include <vector>
#include <string>
#include <limits>
#include <fstream>

using namespace std;

enum class SportType {
    Cricket = 1,
    Football,
    Basketball
};

struct Player {
    string name;
    string role;
    int jerseyNo;
};

struct Team {
    string name;
    vector<Player> players;
};

struct Match {
    int id;
    int teamAIndex;
    int teamBIndex;
    string date;
    string time;
    string venue;

    bool isCompleted = false;
    int winnerIndex = -1;   // -1 = no winner yet / draw
    bool isDraw = false;
    string resultSummary;   // text summary (runs/goals/points etc.)
};

struct Standing {
    string teamName;
    int played = 0;
    int wins = 0;
    int losses = 0;
    int draws = 0;
    int points = 0;
};

class Tournament {
private:
    SportType sport;
    string sportName;
    vector<Team> teams;
    vector<Match> matches;
    int nextMatchId = 1;

public:
    Tournament(SportType s, const string &name) : sport(s), sportName(name) {}

    // ----------------- Helpers -----------------
    void waitAndClear() {
        cout << "\nPress Enter to continue...";
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        cin.get();
    }

    void listTeamsSimple() {
        if (teams.empty()) {
            cout << "No teams available.\n";
            return;
        }
        for (size_t i = 0; i < teams.size(); ++i) {
            cout << i << ") " << teams[i].name << "\n";
        }
    }

    // ====================== FILE HANDLING ======================
    void saveToFile(const string &filename) const {
        ofstream out(filename);
        if (!out) {
            cerr << "Error opening file for writing: " << filename << "\n";
            return;
        }

        // Save Teams
        out << teams.size() << "\n";
        for (const auto &t : teams) {
            out << t.name << "\n";
            out << t.players.size() << "\n";
            for (const auto &p : t.players) {
                out << p.name << "\n";
                out << p.role << "\n";
                out << p.jerseyNo << "\n";
            }
        }

        // Save Matches
        out << matches.size() << "\n";
        for (const auto &m : matches) {
            out << m.id << "\n";
            out << m.teamAIndex << "\n";
            out << m.teamBIndex << "\n";
            out << m.date << "\n";
            out << m.time << "\n";
            out << m.venue << "\n";
            out << m.isCompleted << "\n";
            out << m.winnerIndex << "\n";
            out << m.isDraw << "\n";
            out << m.resultSummary << "\n";
        }

        // Save nextMatchId
        out << nextMatchId << "\n";
    }

    void loadFromFile(const string &filename) {
        ifstream in(filename);
        if (!in) {
            // No file yet (first run) -> start with empty data
            return;
        }

        teams.clear();
        matches.clear();
        nextMatchId = 1;

        string line;

        // Load Teams
        if (!getline(in, line)) return;
        int teamCount = 0;
        try {
            teamCount = stoi(line);
        } catch (...) {
            return;
        }

        for (int i = 0; i < teamCount; ++i) {
            Team t;
            if (!getline(in, t.name)) return;

            if (!getline(in, line)) return;
            int playerCount = 0;
            try {
                playerCount = stoi(line);
            } catch (...) {
                return;
            }

            for (int j = 0; j < playerCount; ++j) {
                Player p;
                if (!getline(in, p.name)) return;
                if (!getline(in, p.role)) return;
                if (!getline(in, line)) return;
                try {
                    p.jerseyNo = stoi(line);
                } catch (...) {
                    p.jerseyNo = 0;
                }
                t.players.push_back(p);
            }
            teams.push_back(t);
        }

        // Load Matches
        if (!getline(in, line)) return;
        int matchCount = 0;
        try {
            matchCount = stoi(line);
        } catch (...) {
            matchCount = 0;
        }

        for (int i = 0; i < matchCount; ++i) {
            Match m;
            if (!getline(in, line)) return;
            try {
                m.id = stoi(line);
            } catch (...) {
                m.id = i + 1;
            }

            if (!getline(in, line)) return;
            m.teamAIndex = stoi(line);

            if (!getline(in, line)) return;
            m.teamBIndex = stoi(line);

            if (!getline(in, m.date)) return;
            if (!getline(in, m.time)) return;
            if (!getline(in, m.venue)) return;

            if (!getline(in, line)) return;
            m.isCompleted = (line == "1" || line == "true");

            if (!getline(in, line)) return;
            m.winnerIndex = stoi(line);

            if (!getline(in, line)) return;
            m.isDraw = (line == "1" || line == "true");

            if (!getline(in, m.resultSummary)) return;

            matches.push_back(m);
        }

        // Load nextMatchId
        if (getline(in, line)) {
            try {
                nextMatchId = stoi(line);
            } catch (...) {
                // If invalid, set based on max match id
                nextMatchId = matchCount + 1;
            }
        } else {
            // If not present, set based on matchCount
            nextMatchId = matchCount + 1;
        }
    }

    // ====================== TEAM MANAGEMENT ======================
    void addTeam() {
        Team t;
        cout << "Enter team name: ";
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        getline(cin, t.name);
        teams.push_back(t);
        cout << "Team added successfully.\n";
    }

    void updateTeam() {
        if (teams.empty()) {
            cout << "No teams to update.\n";
            return;
        }
        cout << "Select team index to update:\n";
        listTeamsSimple();
        int index;
        cout << "Enter index: ";
        cin >> index;
        if (index < 0 || index >= (int)teams.size()) {
            cout << "Invalid index.\n";
            return;
        }
        cout << "Enter new team name: ";
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        getline(cin, teams[index].name);
        cout << "Team updated successfully.\n";
    }

    void deleteTeam() {
        if (teams.empty()) {
            cout << "No teams to delete.\n";
            return;
        }
        cout << "Select team index to delete:\n";
        listTeamsSimple();
        int index;
        cout << "Enter index: ";
        cin >> index;
        if (index < 0 || index >= (int)teams.size()) {
            cout << "Invalid index.\n";
            return;
        }
        teams.erase(teams.begin() + index);
        cout << "Team deleted successfully.\n";
    }

    // ====================== PLAYER MANAGEMENT ======================
    void addPlayer() {
        if (teams.empty()) {
            cout << "No teams available. Add a team first.\n";
            return;
        }
        cout << "Select team index to add player:\n";
        listTeamsSimple();
        int index;
        cout << "Enter index: ";
        cin >> index;
        if (index < 0 || index >= (int)teams.size()) {
            cout << "Invalid index.\n";
            return;
        }

        Player p;
        cout << "Enter player name: ";
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        getline(cin, p.name);
        cout << "Enter player role (Batsman/Goalkeeper etc.): ";
        getline(cin, p.role);
        cout << "Enter jersey number: ";
        cin >> p.jerseyNo;

        teams[index].players.push_back(p);
        cout << "Player added successfully.\n";
    }

    void updatePlayer() {
        if (teams.empty()) {
            cout << "No teams available.\n";
            return;
        }
        cout << "Select team index:\n";
        listTeamsSimple();
        int tIndex;
        cout << "Enter team index: ";
        cin >> tIndex;
        if (tIndex < 0 || tIndex >= (int)teams.size()) {
            cout << "Invalid team index.\n";
            return;
        }

        if (teams[tIndex].players.empty()) {
            cout << "No players in this team.\n";
            return;
        }

        cout << "Players in team " << teams[tIndex].name << ":\n";
        for (size_t i = 0; i < teams[tIndex].players.size(); ++i) {
            cout << i << ") " << teams[tIndex].players[i].name
                 << " | Role: " << teams[tIndex].players[i].role
                 << " | Jersey: " << teams[tIndex].players[i].jerseyNo << "\n";
        }
        int pIndex;
        cout << "Enter player index to update: ";
        cin >> pIndex;
        if (pIndex < 0 || pIndex >= (int)teams[tIndex].players.size()) {
            cout << "Invalid player index.\n";
            return;
        }

        Player &p = teams[tIndex].players[pIndex];
        cout << "Enter new player name: ";
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        getline(cin, p.name);
        cout << "Enter new player role: ";
        getline(cin, p.role);
        cout << "Enter new jersey number: ";
        cin >> p.jerseyNo;

        cout << "Player updated successfully.\n";
    }

    void deletePlayer() {
        if (teams.empty()) {
            cout << "No teams available.\n";
            return;
        }
        cout << "Select team index:\n";
        listTeamsSimple();
        int tIndex;
        cout << "Enter team index: ";
        cin >> tIndex;
        if (tIndex < 0 || tIndex >= (int)teams.size()) {
            cout << "Invalid team index.\n";
            return;
        }

        if (teams[tIndex].players.empty()) {
            cout << "No players in this team.\n";
            return;
        }

        cout << "Players in team " << teams[tIndex].name << ":\n";
        for (size_t i = 0; i < teams[tIndex].players.size(); ++i) {
            cout << i << ") " << teams[tIndex].players[i].name
                 << " | Role: " << teams[tIndex].players[i].role
                 << " | Jersey: " << teams[tIndex].players[i].jerseyNo << "\n";
        }
        int pIndex;
        cout << "Enter player index to delete: ";
        cin >> pIndex;
        if (pIndex < 0 || pIndex >= (int)teams[tIndex].players.size()) {
            cout << "Invalid player index.\n";
            return;
        }

        teams[tIndex].players.erase(teams[tIndex].players.begin() + pIndex);
        cout << "Player deleted successfully.\n";
    }

    // ====================== MATCH CREATION ======================
    void createMatch() {
        if (teams.size() < 2) {
            cout << "At least two teams are required to create a match.\n";
            return;
        }

        cout << "Select Team A index:\n";
        listTeamsSimple();
        int a, b;
        cout << "Enter Team A index: ";
        cin >> a;
        cout << "Enter Team B index: ";
        cin >> b;

        if (a < 0 || a >= (int)teams.size() || b < 0 || b >= (int)teams.size() || a == b) {
            cout << "Invalid team indices.\n";
            return;
        }

        Match m;
        m.id = nextMatchId++;
        m.teamAIndex = a;
        m.teamBIndex = b;

        cout << "Enter match date (e.g. 2025-12-01): ";
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        getline(cin, m.date);
        cout << "Enter match time (e.g. 16:00): ";
        getline(cin, m.time);
        cout << "Enter venue: ";
        getline(cin, m.venue);

        matches.push_back(m);
        cout << "Match created successfully with ID: " << m.id << "\n";
    }

    // ====================== ENTER MATCH RESULTS ======================
    void enterMatchResult() {
        if (matches.empty()) {
            cout << "No matches available.\n";
            return;
        }

        cout << "List of matches:\n";
        for (const auto &m : matches) {
            cout << "Match ID: " << m.id
                 << " | " << teams[m.teamAIndex].name << " vs "
                 << teams[m.teamBIndex].name
                 << " | Date: " << m.date
                 << " | Time: " << m.time
                 << " | Venue: " << m.venue
                 << " | Completed: " << (m.isCompleted ? "Yes" : "No") << "\n";
        }

        int id;
        cout << "Enter Match ID to enter result: ";
        cin >> id;

        int idx = -1;
        for (size_t i = 0; i < matches.size(); ++i) {
            if (matches[i].id == id) {
                idx = (int)i;
                break;
            }
        }

        if (idx == -1) {
            cout << "Invalid Match ID.\n";
            return;
        }

        Match &m = matches[idx];
        cout << "Entering result for: "
             << teams[m.teamAIndex].name << " vs " << teams[m.teamBIndex].name << "\n";

        // Sport-specific input
        if (sport == SportType::Cricket) {
            int runsA, wicketsA, runsB, wicketsB;
            float oversA, oversB;
            cout << "Enter runs scored by " << teams[m.teamAIndex].name << ": ";
            cin >> runsA;
            cout << "Enter wickets lost by " << teams[m.teamAIndex].name << ": ";
            cin >> wicketsA;
            cout << "Enter overs played by " << teams[m.teamAIndex].name << ": ";
            cin >> oversA;

            cout << "Enter runs scored by " << teams[m.teamBIndex].name << ": ";
            cin >> runsB;
            cout << "Enter wickets lost by " << teams[m.teamBIndex].name << ": ";
            cin >> wicketsB;
            cout << "Enter overs played by " << teams[m.teamBIndex].name << ": ";
            cin >> oversB;

            if (runsA > runsB) {
                m.winnerIndex = m.teamAIndex;
                m.isDraw = false;
            } else if (runsB > runsA) {
                m.winnerIndex = m.teamBIndex;
                m.isDraw = false;
            } else {
                m.winnerIndex = -1;
                m.isDraw = true;
            }

            m.resultSummary = "Cricket: " + teams[m.teamAIndex].name + " " + to_string(runsA) +
                              "/" + to_string(wicketsA) + " vs " +
                              teams[m.teamBIndex].name + " " + to_string(runsB) +
                              "/" + to_string(wicketsB);
        } else if (sport == SportType::Football) {
            int goalsA, goalsB;
            cout << "Enter goals scored by " << teams[m.teamAIndex].name << ": ";
            cin >> goalsA;
            cout << "Enter goals scored by " << teams[m.teamBIndex].name << ": ";
            cin >> goalsB;

            if (goalsA > goalsB) {
                m.winnerIndex = m.teamAIndex;
                m.isDraw = false;
            } else if (goalsB > goalsA) {
                m.winnerIndex = m.teamBIndex;
                m.isDraw = false;
            } else {
                m.winnerIndex = -1;
                m.isDraw = true;
            }

            m.resultSummary = "Football: " + teams[m.teamAIndex].name + " " + to_string(goalsA) +
                              " - " + to_string(goalsB) + " " + teams[m.teamBIndex].name;
        } else if (sport == SportType::Basketball) {
            int ptsA, ptsB;
            cout << "Enter points scored by " << teams[m.teamAIndex].name << ": ";
            cin >> ptsA;
            cout << "Enter points scored by " << teams[m.teamBIndex].name << ": ";
            cin >> ptsB;

            if (ptsA > ptsB) {
                m.winnerIndex = m.teamAIndex;
                m.isDraw = false;
            } else if (ptsB > ptsA) {
                m.winnerIndex = m.teamBIndex;
                m.isDraw = false;
            } else {
                m.winnerIndex = -1;
                m.isDraw = true;
            }

            m.resultSummary = "Basketball: " + teams[m.teamAIndex].name + " " + to_string(ptsA) +
                              " - " + to_string(ptsB) + " " + teams[m.teamBIndex].name;
        }

        m.isCompleted = true;
        cout << "Result saved successfully.\n";
    }

    // ====================== POINTS TABLE ======================
    void showPointsTable() {
        if (teams.empty()) {
            cout << "No teams available.\n";
            return;
        }

        vector<Standing> table(teams.size());
        for (size_t i = 0; i < teams.size(); ++i) {
            table[i].teamName = teams[i].name;
        }

        for (const auto &m : matches) {
            if (!m.isCompleted) continue;

            int a = m.teamAIndex;
            int b = m.teamBIndex;

            table[a].played++;
            table[b].played++;

            if (m.isDraw) {
                table[a].draws++;
                table[b].draws++;
                table[a].points += 1;
                table[b].points += 1;
            } else {
                int winner = m.winnerIndex;
                int loser = (winner == a ? b : a);

                table[winner].wins++;
                table[winner].points += 2;
                table[loser].losses++;
            }
        }

        cout << "\n=== Points Table (" << sportName << ") ===\n";
        cout << "Team\tP\tW\tL\tD\tPts\n";
        for (const auto &s : table) {
            cout << s.teamName << "\t"
                 << s.played << "\t"
                 << s.wins << "\t"
                 << s.losses << "\t"
                 << s.draws << "\t"
                 << s.points << "\n";
        }
    }

    // ====================== USER VIEW FUNCTIONS ======================
    void viewTeams() {
        cout << "\n=== Team List (" << sportName << ") ===\n";
        if (teams.empty()) {
            cout << "No teams available.\n";
            return;
        }
        for (size_t i = 0; i < teams.size(); ++i) {
            cout << (i + 1) << ") " << teams[i].name << "\n";
        }
    }

    void viewPlayersInTeam() {
        if (teams.empty()) {
            cout << "No teams available.\n";
            return;
        }
        cout << "Select team index to view players:\n";
        listTeamsSimple();
        int index;
        cout << "Enter index: ";
        cin >> index;
        if (index < 0 || index >= (int)teams.size()) {
            cout << "Invalid index.\n";
            return;
        }

        cout << "\nPlayers in team " << teams[index].name << ":\n";
        if (teams[index].players.empty()) {
            cout << "No players added yet.\n";
            return;
        }
        for (size_t i = 0; i < teams[index].players.size(); ++i) {
            const Player &p = teams[index].players[i];
            cout << (i + 1) << ") " << p.name
                 << " | Role: " << p.role
                 << " | Jersey: " << p.jerseyNo << "\n";
        }
    }

    void viewSchedule() {
        cout << "\n=== Match Schedule (" << sportName << ") ===\n";
        if (matches.empty()) {
            cout << "No matches scheduled.\n";
            return;
        }
        for (const auto &m : matches) {
            cout << "Match ID: " << m.id
                 << " | " << teams[m.teamAIndex].name << " vs "
                 << teams[m.teamBIndex].name
                 << " | Date: " << m.date
                 << " | Time: " << m.time
                 << " | Venue: " << m.venue
                 << " | Completed: " << (m.isCompleted ? "Yes" : "No") << "\n";
        }
    }

    void viewResults() {
        cout << "\n=== Match Results (" << sportName << ") ===\n";
        bool any = false;
        for (const auto &m : matches) {
            if (!m.isCompleted) continue;
            any = true;
            cout << "Match ID: " << m.id
                 << " | " << teams[m.teamAIndex].name << " vs "
                 << teams[m.teamBIndex].name << "\n";
            cout << "Result: " << m.resultSummary << "\n";
            if (m.isDraw) {
                cout << "Outcome: Draw\n";
            } else {
                cout << "Winner: " << teams[m.winnerIndex].name << "\n";
            }
            cout << "--------------------------\n";
        }
        if (!any) {
            cout << "No completed match results yet.\n";
        }
    }

    // ====================== ADMIN MENU ======================
    void adminMenu() {
        int choice;
        do {
            cout << "\n==== ADMIN MENU (" << sportName << ") ====\n";
            cout << "1. Add Team\n";
            cout << "2. Update Team\n";
            cout << "3. Delete Team\n";
            cout << "4. Add Player\n";
            cout << "5. Update Player\n";
            cout << "6. Delete Player\n";
            cout << "7. Create Match\n";
            cout << "8. Enter Match Result\n";
            cout << "9. Generate Points Table\n";
            cout << "10. Back to Main Menu\n";
            cout << "Enter choice: ";
            cin >> choice;

            switch (choice) {
            case 1: addTeam(); break;
            case 2: updateTeam(); break;
            case 3: deleteTeam(); break;
            case 4: addPlayer(); break;
            case 5: updatePlayer(); break;
            case 6: deletePlayer(); break;
            case 7: createMatch(); break;
            case 8: enterMatchResult(); break;
            case 9: showPointsTable(); break;
            case 10: cout << "Returning to main menu...\n"; break;
            default: cout << "Invalid choice.\n"; break;
            }

        } while (choice != 10);
    }

    // ====================== USER MENU ======================
    void userMenu() {
        int choice;
        do {
            cout << "\n==== USER MENU (" << sportName << ") ====\n";
            cout << "1. View Team List\n";
            cout << "2. View Players in a Team\n";
            cout << "3. View Match Schedule\n";
            cout << "4. View Match Results\n";
            cout << "5. View Points Table\n";
            cout << "6. Back to Main Menu\n";
            cout << "Enter choice: ";
            cin >> choice;

            switch (choice) {
            case 1: viewTeams(); break;
            case 2: viewPlayersInTeam(); break;
            case 3: viewSchedule(); break;
            case 4: viewResults(); break;
            case 5: showPointsTable(); break;
            case 6: cout << "Returning to main menu...\n"; break;
            default: cout << "Invalid choice.\n"; break;
            }

        } while (choice != 6);
    }
};

// ----------------- Select Tournament Type -----------------
SportType selectTournamentType() {
    int ch;
    cout << "\nSelect Tournament Type:\n";
    cout << "1. Cricket\n";
    cout << "2. Football\n";
    cout << "3. Basketball\n";
    cout << "Enter choice: ";
    cin >> ch;
    switch (ch) {
    case 1: return SportType::Cricket;
    case 2: return SportType::Football;
    case 3: return SportType::Basketball;
    default:
        cout << "Invalid choice, defaulting to Cricket.\n";
        return SportType::Cricket;
    }
}

int main() {
    Tournament cricket(SportType::Cricket, "Cricket");
    Tournament football(SportType::Football, "Football");
    Tournament basketball(SportType::Basketball, "Basketball");

    // Load saved data (if files exist)
    cricket.loadFromFile("cricket.txt");
    football.loadFromFile("football.txt");
    basketball.loadFromFile("basketball.txt");

    int choice;
    do {
        cout << "\n========= SPORTS TOURNAMENT MANAGEMENT SYSTEM =========\n";
        cout << "1. Admin Mode\n";
        cout << "2. User Mode\n";
        cout << "3. Exit\n";
        cout << "Enter your choice: ";
        cin >> choice;

        if (choice == 1) {
            SportType s = selectTournamentType();
            if (s == SportType::Cricket)
                cricket.adminMenu();
            else if (s == SportType::Football)
                football.adminMenu();
            else
                basketball.adminMenu();
        } else if (choice == 2) {
            SportType s = selectTournamentType();
            if (s == SportType::Cricket)
                cricket.userMenu();
            else if (s == SportType::Football)
                football.userMenu();
            else
                basketball.userMenu();
        } else if (choice == 3) {
            cout << "Saving data and exiting... Goodbye!\n";
        } else {
            cout << "Invalid choice. Try again.\n";
        }

    } while (choice != 3);

    // Save all data before exit
    cricket.saveToFile("cricket.txt");
    football.saveToFile("football.txt");
    basketball.saveToFile("basketball.txt");

    return 0;
}
