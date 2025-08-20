-- Initialize foodie_agents database with basic schema
-- This script runs automatically when the Postgres container starts for the first time

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create basic tables for foodie agents
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS restaurants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    cuisine VARCHAR(100),
    price_range VARCHAR(10),
    rating DECIMAL(3,2),
    review_count INTEGER DEFAULT 0,
    distance DECIMAL(5,2),
    hours JSONB,
    phone VARCHAR(50),
    website TEXT,
    specialties TEXT[],
    dietary_options TEXT[],
    features TEXT[],
    coordinates JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    restaurant_id UUID REFERENCES restaurants(id),
    score DECIMAL(3,2),
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine ON restaurants(cuisine);
CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants(rating);
CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants(city, state);
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_score ON recommendations(score);

-- Insert sample data from restaurants.json
INSERT INTO restaurants (external_id, name, address, city, state, zip_code, cuisine, price_range, rating, review_count, distance, hours, phone, website, specialties, dietary_options, features, coordinates) VALUES
('rest_001', 'La Trattoria', '123 Main St, Downtown', 'San Francisco', 'CA', '94102', 'Italian', '$$', 4.5, 127, 0.8, '{"monday": "11:00 AM - 10:00 PM", "tuesday": "11:00 AM - 10:00 PM", "wednesday": "11:00 AM - 10:00 PM", "thursday": "11:00 AM - 10:00 PM", "friday": "11:00 AM - 11:00 PM", "saturday": "11:00 AM - 11:00 PM", "sunday": "12:00 PM - 9:00 PM"}', '(555) 123-4567', 'https://latrattoria.example.com', ARRAY['Pasta', 'Pizza', 'Wine'], ARRAY['Vegetarian', 'Gluten-free'], ARRAY['Outdoor seating', 'Live music', 'Wine bar'], '{"latitude": 37.7749, "longitude": -122.4194}'),
('rest_002', 'Sakura Sushi', '456 Oak Ave, Midtown', 'San Francisco', 'CA', '94103', 'Japanese', '$$$', 4.8, 89, 1.2, '{"monday": "12:00 PM - 11:00 PM", "tuesday": "12:00 PM - 11:00 PM", "wednesday": "12:00 PM - 11:00 PM", "thursday": "12:00 PM - 11:00 PM", "friday": "12:00 PM - 12:00 AM", "saturday": "12:00 PM - 12:00 AM", "sunday": "12:00 PM - 10:00 PM"}', '(555) 987-6543', 'https://sakura.example.com', ARRAY['Sushi', 'Sashimi', 'Tempura'], ARRAY['Vegetarian', 'Vegan', 'Gluten-free'], ARRAY['Sushi bar', 'Private dining', 'Delivery'], '{"latitude": 37.7694, "longitude": -122.4147}'),
('rest_003', 'Taco Fiesta', '789 Mission Blvd, Mission District', 'San Francisco', 'CA', '94110', 'Mexican', '$', 4.2, 203, 2.1, '{"monday": "10:00 AM - 10:00 PM", "tuesday": "10:00 AM - 10:00 PM", "wednesday": "10:00 AM - 10:00 PM", "thursday": "10:00 AM - 10:00 PM", "friday": "10:00 AM - 11:00 PM", "saturday": "10:00 AM - 11:00 PM", "sunday": "10:00 AM - 9:00 PM"}', '(555) 456-7890', 'https://tacofiesta.example.com', ARRAY['Tacos', 'Burritos', 'Margaritas'], ARRAY['Vegetarian', 'Vegan'], ARRAY['Quick service', 'Takeout', 'Outdoor seating'], '{"latitude": 37.7500, "longitude": -122.4000}'),
('rest_004', 'Golden Dragon', '321 Chinatown Way, Chinatown', 'San Francisco', 'CA', '94108', 'Chinese', '$$', 4.3, 156, 1.5, '{"monday": "11:00 AM - 10:00 PM", "tuesday": "11:00 AM - 10:00 PM", "wednesday": "11:00 AM - 10:00 PM", "thursday": "11:00 AM - 10:00 PM", "friday": "11:00 AM - 11:00 PM", "saturday": "11:00 AM - 11:00 PM", "sunday": "11:00 AM - 9:00 PM"}', '(555) 234-5678', 'https://goldendragon.example.com', ARRAY['Dim Sum', 'Kung Pao Chicken', 'Peking Duck'], ARRAY['Vegetarian', 'Gluten-free'], ARRAY['Dim sum service', 'Private rooms', 'Delivery'], '{"latitude": 37.7941, "longitude": -122.4074}'),
('rest_005', 'Le Bistro', '654 French Quarter, Nob Hill', 'San Francisco', 'CA', '94109', 'French', '$$$$', 4.7, 78, 0.9, '{"monday": "Closed", "tuesday": "6:00 PM - 10:00 PM", "wednesday": "6:00 PM - 10:00 PM", "thursday": "6:00 PM - 10:00 PM", "friday": "6:00 PM - 11:00 PM", "saturday": "6:00 PM - 11:00 PM", "sunday": "6:00 PM - 9:00 PM"}', '(555) 345-6789', 'https://lebistro.example.com', ARRAY['Coq au Vin', 'Beef Bourguignon', 'Crème Brûlée'], ARRAY['Vegetarian'], ARRAY['Fine dining', 'Wine pairing', 'Chef''s table'], '{"latitude": 37.7925, "longitude": -122.4147}')
ON CONFLICT (external_id) DO NOTHING;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_restaurants_updated_at BEFORE UPDATE ON restaurants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE foodie_agents TO foodie_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO foodie_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO foodie_user;
