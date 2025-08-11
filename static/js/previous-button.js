// Function to navigate to previous step
function goToPreviousStep() {
    const currentStep = parseInt(window.currentStep);
    if (currentStep > 1) {
        const previousStep = currentStep - 1;
        window.location.href = `${window.location.pathname}?step=${previousStep}`;
    }
}
