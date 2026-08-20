// This is your Prisma schema file,
// learn more about it in the docs: https://pris.ly/d/prisma-schema

//*****************************************************/
//******************** DB CONFIG **********************/
//*****************************************************/

generator client {
  provider             = "prisma-client-py"
  recursive_type_depth = 5
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

//*****************************************************/
//******************** Users ***************************/
//*****************************************************/

model User {
  id       Int      @id @default(autoincrement())
  pubkey   String   @unique
  email    String   @unique
  password String
  role     UserRoleEnum @default(CANDIDATE)
  isActive Boolean  @default(true)

  candidateProfile CandidateProfile?
  coordinateur     Coordinateur?
  administrateur   Administrateur?

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_USERS")
}

//*****************************************************/
//******************** Candidat *************************/
//*****************************************************/

model CandidateProfile {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  userId Int  @unique
  user   User @relation(fields: [userId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  nom            String
  prenom         String
  cin            String @unique
  email          String
  telephone      String
  ville          String
  anneeNaissance Int
  statut         CandidateStatusEnum @default(EN_ATTENTE)

  diplome      Diplome?
  licenceYears LicenceYear[]
  master1Year  Master1Year?
  redoublement Redoublement?
  applications Application[]

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_CANDIDATE_PROFILES")
}

model TypeLicence {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  intitule    String
  domaine     String
  estEligible Boolean @default(true)

  diplomes Diplome[]
  masters  Master[]  @relation("MasterTypeLicence")

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_TYPE_LICENCES")
}

model LicenceYear {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  candidateProfileId Int
  candidateProfile   CandidateProfile @relation(fields: [candidateProfileId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  annee              Int
  anneeUniversitaire String
  moyenne            Float

  releve Document? @relation("LicenceYearReleve")

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_LICENCE_YEARS")
}

model Diplome {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  candidateProfileId Int    @unique
  candidateProfile   CandidateProfile @relation(fields: [candidateProfileId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  typeLicenceId Int
  typeLicence   TypeLicence @relation(fields: [typeLicenceId], references: [id], onUpdate: Cascade)

  anneeObtention String
  universite     String

  pdf Document? @relation("DiplomePdf")

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_DIPLOMES")
}

model Master1Year {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  candidateProfileId Int    @unique
  candidateProfile   CandidateProfile @relation(fields: [candidateProfileId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  anneeUniversitaire String
  moyenne            Float
  etablissement      String

  releveM1 Document? @relation("Master1YearReleve")

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_MASTER1_YEARS")
}

model Redoublement {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  candidateProfileId Int    @unique
  candidateProfile   CandidateProfile @relation(fields: [candidateProfileId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  aRedouble Boolean @default(false)

  redoublementYears RedoublementYear[]

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_REDOUBLEMENTS")
}

model RedoublementYear {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  redoublementId Int
  redoublement   Redoublement @relation(fields: [redoublementId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  annee String

  justificatifs Document[] @relation("RedoublementYearJustificatifs")

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_REDOUBLEMENT_YEARS")
}

//*****************************************************/
//******************** Documents ************************/
//*****************************************************/

model Document {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  nom  String
  type DocumentTypeEnum
  url  String

  licenceYearId Int?     @unique
  licenceYear   LicenceYear? @relation("LicenceYearReleve", fields: [licenceYearId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  diplomeId Int?    @unique
  diplome   Diplome? @relation("DiplomePdf", fields: [diplomeId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  master1YearId Int?     @unique
  master1Year   Master1Year? @relation("Master1YearReleve", fields: [master1YearId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  redoublementYearId Int?
  redoublementYear   RedoublementYear? @relation("RedoublementYearJustificatifs", fields: [redoublementYearId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  createdAt DateTime? @default(now())
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_DOCUMENTS")
}

//*****************************************************/
//******************** Masters ***************************/
//*****************************************************/

model Master {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  nom          String
  universite   String
  ville        String
  domaine      String
  discipline   String
  nombrePlaces Int
  dateDebut    DateTime
  dateFin      DateTime
  statut       MasterStatusEnum @default(BROUILLON)

  coordinateurId Int
  coordinateur   Coordinateur @relation(fields: [coordinateurId], references: [id], onUpdate: Cascade)

  administrateurId Int?
  administrateur   Administrateur? @relation(fields: [administrateurId], references: [id], onUpdate: Cascade)

  eligibilityCriteria   EligibilityCriteria[]
  scoreFormula          ScoreFormula?
  requiredDocuments     RequiredDocument[]
  applications          Application[]
  typeLicencesAcceptees TypeLicence[]         @relation("MasterTypeLicence")

  // Passerelle M1 -> M2 (auto-relation many-to-many)
  passerellesVers   Master[] @relation("MasterPasserelle")
  passerellesDepuis Master[] @relation("MasterPasserelle")

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_MASTERS")
}

model EligibilityCriteria {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  masterId Int
  master   Master @relation(fields: [masterId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  type        String
  valeur      String
  obligatoire Boolean @default(true)

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_ELIGIBILITY_CRITERIA")
}

model ScoreFormula {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  masterId Int    @unique
  master   Master @relation(fields: [masterId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  criteria ScoreCriterion[]

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_SCORE_FORMULAS")
}

model ScoreCriterion {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  scoreFormulaId Int
  scoreFormula   ScoreFormula @relation(fields: [scoreFormulaId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  critere String
  poids   Float

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_SCORE_CRITERIA")
}

model RequiredDocument {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  masterId Int
  master   Master @relation(fields: [masterId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  type String

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_REQUIRED_DOCUMENTS")
}

//*****************************************************/
//******************** Candidatures **********************/
//*****************************************************/

model Application {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  candidateProfileId Int
  candidateProfile   CandidateProfile @relation(fields: [candidateProfileId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  masterId Int
  master   Master @relation(fields: [masterId], references: [id], onUpdate: Cascade)

  niveau         String
  dateSoumission DateTime @default(now())
  score          Float?
  statut         ApplicationStatusEnum @default(SOUMISE)

  notifications NotificationRecord[]

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_APPLICATIONS")
}

model NotificationRecord {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  applicationId Int
  application   Application @relation(fields: [applicationId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  motif            String
  documentConcerne String?
  objet            String
  corps            String
  envoyeeLe        DateTime @default(now())

  createdAt DateTime? @default(now())
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_NOTIFICATION_RECORDS")
}

//*****************************************************/
//******************** Personnel ***********************/
//*****************************************************/

model Coordinateur {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  userId Int  @unique
  user   User @relation(fields: [userId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  nom   String
  email String @unique

  masters Master[]

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_COORDINATEURS")
}

model Administrateur {
  id     Int    @id @default(autoincrement())
  pubkey String @unique

  userId Int  @unique
  user   User @relation(fields: [userId], references: [id], onDelete: Cascade, onUpdate: Cascade)

  nom   String
  email String @unique

  masters Master[]

  createdAt DateTime? @default(now())
  updatedAt DateTime? @updatedAt
  deletedAt DateTime? @db.Timestamp()

  @@map("MST_ADMINISTRATEURS")
}

//*****************************************************/
//******************** ENUMS **************************/
//*****************************************************/

enum UserRoleEnum {
  CANDIDATE
  COORDINATOR
  ADMIN
}

enum CandidateStatusEnum {
  EN_ATTENTE
  VALIDE
  REJETE
}

enum DocumentTypeEnum {
  RELEVE_NOTES
  DIPLOME
  JUSTIFICATIF
  AUTRE
}

enum MasterStatusEnum {
  OUVERT
  FERME
  BROUILLON
}

enum ApplicationStatusEnum {
  SOUMISE
  EN_COURS
  ACCEPTEE
  REJETEE
}