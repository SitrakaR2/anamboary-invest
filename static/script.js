document.addEventListener('DOMContentLoaded', function() {
    const investForm = document.getElementById('investForm');
    if (investForm) {
        investForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const amount = document.getElementById('amount').value;
            const response = await fetch('/dashboard', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ amount })
            });

            if (response.ok) {
                const data = await response.json();
                document.getElementById('balance').textContent = data.balance.toFixed(2) + " Ar";

                alert("Investissement réussi !");
                location.reload();
            } else {
                const error = await response.text();
                alert(error);
            }
        });
    }
});
