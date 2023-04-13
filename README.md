# TherapistGPT: An Open-Source Framework for Building Digital Therapists

TherapistGPT is an open-source framework designed to help researchers and developers create digital psychotherapists using Python. By providing a common architecture, we aim to foster collaboration and improve the state of the art in digital therapy.

With a focus on accessibility and ease of use, our framework offers a solid foundation for building digital therapists that can adapt to various therapy types and client needs. The code is easily editable, allowing developers to customize and extend the functionality as needed.

As privacy is our top priority, TherapistGPT does not include database management. This ensures that developers can implement their own secure solutions, adhering to their specific country or region's legislation.

Discover the potential of TherapistGPT by trying the demo at [therapist.digital](http://therapist.digital).

## Table of Contents

- [🚀 Features](#-features)
- [📋 Requirements](#-requirements)
- [💾 Installation](#-installation)
- [🔧 Usage](#-usage)
  - [Configuration](#configuration)
  - [Adapting to Different Therapy Types](#adapting-to-different-therapy-types)
  - [Client Information and Anamnesis](#client-information-and-anamnesis)
  - [Evaluation and Therapy Progress](#evaluation-and-therapy-progress)
- [🌟 Contributing](#-contributing)
- [⚠️ Limitations](#-limitations)
- [🛡️ Disclaimer](#️-disclaimer)
- [📢 Connect with Us on Social Media](#-connect-with-us-on-social-media)

## 🚀 Features

- Open-source and easily editable Python code
- Common architecture for building digital therapists
- Supports Cognitive Behavioral Therapy (CBT), Dialectical Behavior Therapy (DBT), and Psychodynamic Therapy
- Adapts to client information, demands, and anamnesis
- Evidence-based information about therapy types
- Regular evaluation and anamnesis updates during therapy sessions
- No fine-tuning required; works with prompt-engineering

## 📋 Requirements

- Python 3.9
- OpenAI API key (preferably with GPT-4 access)
- [Redis server](https://redis.io/download/) 

## 💾 Installation

1. Clone the repository:

```
git clone https://github.com/nmichaud0/TherapistGPT.git
```

2. Navigate to the project directory:

```
cd TherapistGPT
```

3. Create a new Python virtual environment and activate it:

```
python -m venv /venv
source venv/bin/activate
```

4. Install the required dependencies:

```
pip install -r requirements.txt
```

5. Open a new terminal window and run your redis server:

```
redis-server
```

6. Open another terminal window, navigate to the project directory, activate the virtual environment and run a celery worker:

```
source venv/bin/activate
TherapistGPT % celery -A TherapistGPT worker --loglevel=info
```

7. Open another terminal window, navigate to the project directory, activate the environment and run the Django server:

```
python manage.py runserver
```

8. Connect to the local website at : http://127.0.0.1:8000/

9. Add your own OpenAI API key with the blue "+" button and you're good to go.

## 🔧 Usage

### Configuration

All configurations can be done on the client side, including API key handling, model version selection, and customization of therapy types.

### Adapting to Different Therapy Types

TherapistGPT provides support for various therapy types, including Cognitive Behavioral Therapy (CBT), Dialectical Behavior Therapy (DBT), and Psychodynamic Therapy. The framework adapts to the specific requirements of each therapy type, ensuring a personalized experience for clients.

### Client Information and Anamnesis

The framework gathers client information and demands, then infers the most suitable therapy type for each client. It also maintains an ongoing anamnesis throughout the therapy process, ensuring that the digital therapist has a comprehensive understanding of the client's history and progress.

### Evaluation and Therapy Progress

TherapistGPT regularly evaluates the therapy's effectiveness and updates the anamnesis accordingly. This allows the digital therapist to adapt its approach as needed and ensure that the therapy remains focused on the client's needs and goals.

When the client's demand is fulfilled, the therapy session ends, marking a successful conclusion to the therapeutic process.

## 🌟 Contributing

We welcome and encourage contributions to TherapistGPT! If you're interested in improving the framework, adding new features, or fixing bugs, please feel free to submit issues and pull requests on GitHub.

Make sure to follow our contribution guidelines and adhere to our code of conduct to ensure a positive and inclusive environment for all contributors.

## ⚠️ Limitations

TherapistGPT is a research experiment designed to showcase the potential of digital therapists built on a common architecture. As such, it may have limitations and may not perform optimally in complex, real-world scenarios.

Before deploying TherapistGPT in a production environment or using it to provide therapy services, we strongly recommend thorough testing and customization to ensure that it meets the specific requirements of your use case.

## 🛡️ Disclaimer

TherapistGPT is an experimental project aimed at providing a foundation for building digital psychotherapists. It is not a complete, polished product, and its usage comes with inherent risks. By using this software, you agree to assume all risks associated with its use, including but not limited to data loss, system failure, or any other issues that may arise.

The developers and contributors of TherapistGPT do not accept any responsibility or liability for any losses, damages, or other consequences that may occur as a result of using this software. You are solely responsible for any decisions and actions taken based on the information provided by TherapistGPT.

Please ensure that any adaptations and deployments of TherapistGPT comply with privacy and security standards, as well as the specific legislation of the country or region where the digital therapist will be used.

## 📢 Connect with Us on Social Media

Stay up-to-date with the latest news, updates, and insights about TherapistGPT by following our social media accounts:

- [Twitter](https://twitter.com/nizarmichaud_)
- [Instagram](https://instagram.com/nizarmichaud)

We look forward to connecting with you and hearing your thoughts, ideas, and experiences with TherapistGPT.

## TODO:

- Worker timeout-3000ms on Heroku --> queue requests for web deploy
