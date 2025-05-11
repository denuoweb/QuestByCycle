import Shepherd from 'https://cdn.jsdelivr.net/npm/shepherd.js@13.0.0/dist/esm/shepherd.mjs';

document.addEventListener('DOMContentLoaded', () => {
  const onboardingStatusElement = document.getElementById('onboardingStatus');
  const startOnboarding = onboardingStatusElement ? onboardingStatusElement.getAttribute('data-start-onboarding') === 'true' : false;

  const tour = new Shepherd.Tour({
    useModalOverlay: true,
    defaultStepOptions: {
      classes: 'shepherd-theme-custom',
      scrollTo: false,
      canClickTarget: false,
      buttons: [
        {
          text: 'Next',
          action: () => {
            tour.next();
            updateStepCounter();
          }
        }
      ]
    }
  });

  const steps = [
    {
      id: 'introduction',
      text: 'Welcome to Quest by Cycle! Ready to start your journey? Please fill out your profile!',
      attachTo: { on: 'top' },
      modalOverlayOpeningPadding: 10,
      modalOverlayOpeningRadius: 8,
    },
    {
      id: 'view-profile',
      text: 'Access your profile here.',
      attachTo: { element: '#view-profile-button', on: 'top' },
      scrollTo: true,
      buttons: [
        {
          text: 'Next',
          action: () => {
            document.getElementById('view-profile-button').click();
            setTimeout(() => {
              tour.next();
              updateStepCounter();
              markOnboardingComplete();
              tour.complete();
            }, 200);
          }
        }
      ]
    }
  ];

  // Add steps to the tour
  steps.forEach((step, index) => {
    step.buttons = step.buttons || [
      {
        text: `Next (${index + 1}/${steps.length})`,
        action: () => {
          tour.next();
          updateStepCounter();
        }
      }
    ];
    tour.addStep(step);
  });

  function updateStepCounter() {
    const currentStep = tour.getCurrentStep();
    if (currentStep && currentStep.buttons && currentStep.buttons.length > 0) {
      const currentIndex = steps.findIndex(step => step.id === currentStep.id) + 1;
      const totalSteps = steps.length;
      const nextButton = currentStep.buttons[0].text;
      if (nextButton.includes('Next')) {
        currentStep.updateButton(0, { text: `Next (${currentIndex}/${totalSteps})` });
      }
    }
  }


  // Start the tour automatically if needed
  if (startOnboarding) {
    tour.start();
  }

  // Function to send a request to mark onboarding as complete
  function markOnboardingComplete() {
    const userIdMeta = document.querySelector('meta[name="current-user-id"]');
    const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
    
    if (!userIdMeta || !csrfTokenMeta) {
      console.error('Meta tags for user ID or CSRF token not found.');
      return;
    }

    const userId = userIdMeta.getAttribute('content');
    const csrfToken = csrfTokenMeta.getAttribute('content');

    fetch('/mark-onboarding-complete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify(userId)
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
      } else {
        console.error('Failed to mark onboarding as complete.');
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }

  const restartTourLink = document.getElementById('restart-tour-link');
  if (restartTourLink) {
    restartTourLink.addEventListener('click', () => {
      tour.start();
      updateStepCounter();
    });
  }
});
