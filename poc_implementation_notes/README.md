# Σημειώσεις Υλοποίησης PoC

Ο φάκελος αυτός περιέχει τεχνικά κείμενα εργασίας για την υλοποίηση του `PoC` σε `Django`.

Συγκεντρώνει:

- αντιστοίχιση των reference scripts προς `Django management commands`
- προτεινόμενη δομή έργου
- προτεινόμενο outline για τα βασικά models
- προτεινόμενο response contract ανάμεσα σε backend και διεπαφή

Τα κείμενα αυτά διαβάζονται καλύτερα ως συμπληρωματικά και όχι ως ανεξάρτητα έγγραφα.

## Περιεχόμενα

- `django_commands_mapping.md`
  - αντιστοίχιση reference scripts προς `Django management commands` και βασική σειρά εκτέλεσης
- `django_project_structure.md`
  - προτεινόμενη δομή `Django` έργου, apps, services και command paths
- `django_models_outline.md`
  - προτεινόμενο outline για models, σχέσεις, statuses, constraints και ενδεικτικά model examples
- `api_response_contract.md`
  - προτεινόμενο ελάχιστο response shape για `search` και `assistant` mode

## Προτεινόμενη σειρά ανάγνωσης

1. `django_commands_mapping.md`
   για να γίνει σαφές ποια βήματα πρέπει να υλοποιηθούν και με ποια λογική θα εκτελούνται
2. `django_project_structure.md`
   για να οριστεί πού θα μπει κάθε ευθύνη μέσα στο `Django` project
3. `django_models_outline.md`
   για να οριστεί πώς αποτυπώνονται τα βασικά δεδομένα, οι σχέσεις και τα statuses στη βάση
4. `api_response_contract.md`
   για να οριστεί τι ακριβώς επιστρέφει το backend προς τη διεπαφή σε `search` και `assistant` mode

## Πώς συνδέονται μεταξύ τους

- το `django_commands_mapping.md` απαντά στο ερώτημα "ποια commands χρειαζόμαστε"
- το `django_project_structure.md` απαντά στο ερώτημα "σε ποια apps και services θα ανήκουν"
- το `django_models_outline.md` απαντά στο ερώτημα "με ποια models και σχέσεις θα αποθηκεύονται τα δεδομένα"
- το `api_response_contract.md` απαντά στο ερώτημα "με ποιο ελάχιστο σχήμα δεδομένων θα επικοινωνεί το backend με τη διεπαφή"

Ο φάκελος αυτός δεν περιέχει εκτελέσιμα scripts. Τα εκτελέσιμα αρχεία παραμένουν στον φάκελο `reference_scripts/`.
