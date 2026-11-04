import {FileSpreadsheet,FileText,Download,Mail,RefreshCw,Eye} from 'lucide-react';
const icons={FileSpreadsheet,FileText,Download,Mail,RefreshCw,Eye};
export default function ActionGlyph({name}:{name:keyof typeof icons}){const Icon=icons[name];return <Icon size={19} aria-hidden="true"/>}
