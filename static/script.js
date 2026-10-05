// ================= E-WASTE MANAGEMENT =================

console.log("EcoRecycle E-Waste Management System loaded.");


// Set today's date as the minimum pickup date

const dateInput = document.getElementById("pickup_date");

if (dateInput) {

    const today = new Date();

    const year = today.getFullYear();

    const month = String(
        today.getMonth() + 1
    ).padStart(2, "0");

    const day = String(
        today.getDate()
    ).padStart(2, "0");

    const currentDate =
        year + "-" + month + "-" + day;

    dateInput.min = currentDate;
}