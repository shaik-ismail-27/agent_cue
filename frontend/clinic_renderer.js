// Clinic Renderer for Enhanced Display
class ClinicRenderer {
    static renderClinicCard(clinic, index) {
        console.log('Rendering clinic card:', clinic);
        
        const price = clinic.price_list?.["General Medicine"] || clinic.price_list?.["Family Medicine"] || 0;
        const isFree = price === 0;
        
        console.log('Clinic doctors:', clinic.doctors);
        
        let doctorsHtml = '';
        if (clinic.doctors && clinic.doctors.length > 0) {
            doctorsHtml = `
                <div class="doctors-section">
                    <div class="doctors-title">
                        <i class="fas fa-user-md"></i> Available Doctor
                    </div>
                    ${this.renderDoctorCard(clinic.doctors[0])}
                </div>
            `;
        }
        
        return `
            <div class="clinic-card" data-clinic-index="${index}">
                <div class="clinic-header">
                    <div>
                        <div class="clinic-name">${index + 1}. ${clinic.name}</div>
                        <div class="clinic-rating">
                            <i class="fas fa-star"></i>
                            <span>${clinic.rating} ${clinic.rating >= 4.5 ? 'Excellent' : clinic.rating >= 4.0 ? 'Good' : 'Fair'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="clinic-info">
                    <div class="clinic-info-item">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${clinic.address}</span>
                    </div>
                    <div class="clinic-info-item">
                        <i class="fas fa-clock"></i>
                        <span>${clinic.waiting_time}</span>
                    </div>
                    <div class="clinic-info-item">
                        <i class="fas fa-calendar-alt"></i>
                        <span>${clinic.hours}</span>
                    </div>
                    <div class="clinic-info-item">
                        <i class="fas fa-hand-holding-medical"></i>
                        <span>${clinic.specializations?.join(', ') || 'General Practice'}</span>
                    </div>
                </div>
                
                <div class="clinic-price ${isFree ? 'free' : ''}">
                    ${isFree ? 
                        '<i class="fas fa-gift"></i> FREE - No payment required' : 
                        `<i class="fas fa-rupee-sign"></i> ${price} consultation fee`
                    }
                </div>
                
                ${doctorsHtml}
            </div>
        `;
    }
    
    static renderDoctorCard(doctor) {
        console.log('Rendering doctor card for:', doctor);
        
        const languages = doctor.languages ? doctor.languages.slice(0, 2).join(', ') : 'English';
        const rating = doctor.rating || '4.5';
        const imageUrl = doctor.image || `https://picsum.photos/seed/doctor${doctor.id}/200/200.jpg`;
        
        console.log('Doctor image URL:', imageUrl);
        
        return `
            <div class="doctor-card">
                <img src="${imageUrl}" alt="${doctor.name}" class="doctor-avatar" 
                     onerror="console.log('Image failed to load for ${doctor.name}'); this.src='https://picsum.photos/seed/defaultdoctor/200/200.jpg'"
                     onload="console.log('Image loaded successfully for ${doctor.name}')">
                <div class="doctor-info">
                    <div class="doctor-name">${doctor.name}</div>
                    <div class="doctor-details">${doctor.specialization} &bull; ${doctor.experience}</div>
                    <div class="doctor-details">${doctor.education}</div>
                    <div class="doctor-meta">
                        <div class="doctor-meta-item doctor-rating">
                            <i class="fas fa-star"></i>
                            <span>${rating}</span>
                        </div>
                        <div class="doctor-meta-item">
                            <i class="fas fa-language"></i>
                            <span>${languages}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    static renderClinicsList(clinics) {
        console.log('Rendering clinics list:', clinics);
        
        if (!clinics || clinics.length === 0) {
            console.log('No clinics found');
            return '<p>No clinics found matching your criteria.</p>';
        }
        
        return clinics.map((clinic, index) => this.renderClinicCard(clinic, index)).join('');
    }
    
    static detectAndRenderClinics(message) {
        // Check if message contains clinic information
        if (message.includes('Rating:') && message.includes('Address:') && message.includes('Price:')) {
            // This looks like a clinic response, try to enhance it
            return this.enhanceClinicMessage(message);
        }
        return message;
    }
    
    static enhanceClinicMessage(message) {
        // For now, return the original message with enhanced formatting
        // In a real implementation, you would parse the message and extract clinic data
        return message;
    }
}

// Make it available globally
window.ClinicRenderer = ClinicRenderer;
