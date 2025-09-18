const ParticipatesInsForms = document.querySelectorAll(
  "[participates-ins-form]",
);
// const documentListElement = document.getElementById("documentList");
// const courseId = document.body.dataset.courseId
//   ? Number(document.body.dataset.courseId)
//   : null;

// if (courseId === null) {
//   throw Error("Course ID not present as datum on body tag.");
// }

// async function loadDocumentList() {
//   documentListElement.innerHTML = "";
//   const documentList = document.createElement("ul");
//   documentListElement.appendChild(documentList);

//   fetch(`/documents?course_id=${courseId}`, {
//     method: "GET",
//     headers: {
//       "Content-Type": "application/json",
//       "Accept": "application/json",
//     },
//   }).then((response) => {
//     if (!response.ok) {
//       throw Error("Could not load course documents.");
//     }
//     return response.json();
//   }).then((data) => {
//     if (data.documents.length === 0) {
//       const noDocsMessage = document.createElement("p");
//       noDocsMessage.textContent = "No documents uploaded yet.";
//       documentListElement.appendChild(noDocsMessage);
//       return;
//     }
//     for (const doc of data.documents) {
//       const listItem = document.createElement("li");
//       const link = document.createElement("a");
//       const deleteButton = document.createElement("button");
//       deleteButton.setAttribute("delete-object", doc.url);
//       link.href = doc.url;
//       link.textContent = doc.filename;
//       deleteButton.textContent = "Delete";
//       listItem.appendChild(link);
//       listItem.appendChild(deleteButton);
//       documentList.appendChild(listItem);
//     }
//     addDeleteEventListeners();
//   }).catch((error) => {
//     console.error("Error loading documents:", error);
//     const errorMessage = document.createElement("p");
//     errorMessage.textContent = "Error loading documents.";
//     documentListElement.appendChild(errorMessage);
//   });
// }

/**
 * Retuns the emails from a CSV string.
 * The emails and the header for the email column must not have commas in them.
 * @param {string} csv_text The CSV text.
 * @param {string} email_column The name of the column that contains the emails.
 * @param {string} email_suffix The suffix to be appended to each email. Should probably start with '@'
 * @returns {Array<string>} the emails
 */
function emails_from_csv(csv_text, email_column, email_suffix = "@ucr.edu") {
  const lines = csv_text.split("\n").map(
    (line) =>
      line.replace(
        /"(.*?)"/g,
        (_, captured) => {
          return `"${captured.replace(",", "")}"`;
        },
      ),
  );
  const header = lines.shift().split(",");
  const email_column_index = header.indexOf(email_column);
  return lines.map((line) => line.split(",")[email_column_index] + email_suffix)
    .filter((email) => email.length > email_suffix.length);
}

function disableUploadButton() {
  const button = document.getElementById("uploadButton");
  button.disabled = true;
  button.value = "Uploading...";
}

document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        if (event.target.tagName === "INPUT") {
          event.preventDefault();
        }
      }
    });
  });
});

ParticipatesInsForms.forEach((form) => {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const csv_file = formData.get("file");
    const course_id = formData.get("course_id");
    const role = formData.get("role");
    const email_column = "SIS User ID";
    const email_suffix = "@ucr.edu";

    if (!csv_file) {
      alert("Please upload a CSV file.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const csv_text = reader.result;
      const emails = emails_from_csv(csv_text, email_column, email_suffix);
      if (emails.length === 0) {
        alert(
          `No emails found in the CSV file. Please check that the column containing the emails has the name '${email_column}'.`,
        );
        return;
      }

      fetch("/participates_ins", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          course_id: course_id,
          role: role,
          email: emails,
        }),
      }).then(async (response) => {
        if (!response.ok) {
          throw Error("Could not add participants.");
        }
        alert("CSV processed successfully.");
        window.location.reload();
      }).catch((error) => {
        console.error("Error adding participants:", error);
        alert("Error adding participants.");
      });
    };
    reader.readAsText(csv_file);
  });
});

// loadDocumentList();
