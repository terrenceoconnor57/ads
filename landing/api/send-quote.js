import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export default async function handler(req, res) {
    // Only allow POST requests
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const { name, email, phone, service, details } = req.body;

        // Validate required fields
        if (!name || !email || !phone) {
            return res.status(400).json({ error: 'Name, email, and phone are required' });
        }

        // Format the service name for display
        const serviceLabels = {
            'furniture': 'Furniture Removal', 
            'appliances': 'Appliance Removal',
            'yard': 'Yard Waste',
            'construction': 'Construction Debris',
            'cleanout': 'Full Cleanout',
            'other': 'Other'
        };
        const serviceName = serviceLabels[service] || 'Not specified';

        // Build the email content
        const emailHtml = `
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f97316; margin-bottom: 24px;">New Quote Request</h1>
                
                <div style="background: #f4f4f5; border-radius: 8px; padding: 24px; margin-bottom: 24px;">
                    <h2 style="margin-top: 0; color: #18181b;">Contact Information</h2>
                    <p style="margin: 8px 0;"><strong>Name:</strong> ${escapeHtml(name)}</p>
                    <p style="margin: 8px 0;"><strong>Email:</strong> <a href="mailto:${escapeHtml(email)}">${escapeHtml(email)}</a></p>
                    <p style="margin: 8px 0;"><strong>Phone:</strong> <a href="tel:${escapeHtml(phone)}">${escapeHtml(phone)}</a></p>
                </div>
                
                <div style="background: #f4f4f5; border-radius: 8px; padding: 24px;">
                    <h2 style="margin-top: 0; color: #18181b;">Request Details</h2>
                    <p style="margin: 8px 0;"><strong>Service:</strong> ${escapeHtml(serviceName)}</p>
                    <p style="margin: 8px 0;"><strong>Details:</strong></p>
                    <p style="margin: 8px 0; white-space: pre-wrap;">${details ? escapeHtml(details) : 'No additional details provided'}</p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #e4e4e7; margin: 24px 0;">
                
                <p style="color: #71717a; font-size: 14px;">
                    This quote request was submitted from your landing page.
                </p>
            </div>
        `;

        const emailText = `
New Quote Request

Contact Information:
- Name: ${name}
- Email: ${email}
- Phone: ${phone}

Request Details:
- Service: ${serviceName}
- Details: ${details || 'No additional details provided'}
        `.trim();

        // Send email via Resend
        const { data, error } = await resend.emails.send({
            from: 'Quote Request <onboarding@resend.dev>',
            to: ['terrenceoconnor57@gmail.com'],
            subject: `New Quote Request from ${name}`,
            html: emailHtml,
            text: emailText,
            reply_to: email
        });

        if (error) {
            console.error('Resend error:', error);
            return res.status(500).json({ error: 'Failed to send email. Please try again.' });
        }

        return res.status(200).json({ success: true, id: data.id });

    } catch (error) {
        console.error('Server error:', error);
        return res.status(500).json({ error: 'An unexpected error occurred. Please try again.' });
    }
}

// Helper function to escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
